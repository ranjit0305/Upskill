from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from app.models.company import Company, InterviewFeedback, CompanyInsights, InsightMetadata, RoundDetail, TechnicalQuestionDetail
from app.services.company_service import CompanyService
from app.services.document_processor import DocumentProcessor
from app.models.user import UserRole
import os
import shutil
from datetime import datetime
import logging

router = APIRouter(prefix="/companies", tags=["Companies"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user"""
    from app.services.auth_service import AuthService
    return await AuthService.get_current_user(credentials.credentials)

UPLOAD_DIR = "uploads/feedback"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _merge_unique_tags(existing_tags: List[str], new_tags: List[str]) -> List[str]:
    merged = []
    seen = set()
    for tag in (existing_tags or []) + (new_tags or []):
        cleaned = str(tag).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(cleaned)
    return merged


async def _save_generated_questions(
    question_payloads: List[dict],
    company_id: str,
    uploader_id: str,
    company_name: str,
    source: str
) -> int:
    from app.models.assessment import Question

    saved_count = 0
    source_tags = [f"source:{source}", "company_specific", f"company_id:{company_id}"]
    if company_name:
        source_tags.append(f"company_name:{company_name.lower().replace(' ', '-')}")

    for q_data in question_payloads:
        question_text = (q_data.get("text") or "").strip()
        if not question_text:
            continue

        tags = _merge_unique_tags(q_data.get("tags", []), source_tags)
        existing_q = await Question.find_one({
            "question": question_text,
            "companies": company_id,
            "tags": {"$in": [f"source:{source}"]}
        })

        if not existing_q:
            new_q = Question(
                type=q_data.get("type", "technical"),
                category=q_data.get("category", "technical"),
                difficulty=q_data.get("difficulty", "medium"),
                question=question_text,
                options=q_data.get("options") or [],
                correct_answer=q_data.get("correct_answer", "Refer to explanation"),
                explanation=q_data.get("explanation", f"Derived from {source} content for {company_name}."),
                tags=tags,
                companies=[company_id],
                test_cases=q_data.get("test_cases"),
                sample_input=q_data.get("sample_input"),
                sample_output=q_data.get("sample_output"),
                created_by=uploader_id,
                is_generated=True
            )
            await new_q.insert()
            saved_count += 1
        else:
            merged_tags = _merge_unique_tags(existing_q.tags, tags)
            if merged_tags != existing_q.tags:
                existing_q.tags = merged_tags
                await existing_q.save()

    return saved_count


async def _auto_enrich_company_questions(company: Company, uploader_id: str) -> int:
    from app.models.assessment import Question
    from app.services.ai_service import AIService
    from app.services.scraper_service import ScraperService

    existing_count = await Question.find({
        "companies": company.id.__str__(),
        "tags": {"$in": ["source:feedback", "source:web"]}
    }).count()

    if existing_count >= 12:
        return 0

    urls = await ScraperService.discover_interview_links(company.name, limit=2)
    if not urls:
        return 0

    added = 0
    for url in urls:
        try:
            extracted_questions = await AIService.extract_questions_from_url(
                url,
                str(company.id),
                uploader_id,
                company_name=company.name,
                source="web"
            )
            added += await _save_generated_questions(
                extracted_questions,
                str(company.id),
                uploader_id,
                company.name,
                source="web"
            )
        except Exception as exc:
            logger.warning("Auto enrichment failed for %s: %s", url, exc)

    return added

@router.get("", response_model=List[Company])
async def get_companies():
    """List all available companies"""
    return await Company.find_all().to_list()

@router.get("/{company_id}/dashboard")
async def get_company_dashboard(company_id: str, user_id: str):
    """Get preparation dashboard for a specific company"""
    dashboard_data = await CompanyService.get_company_prep_dashboard(user_id, company_id)
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Company not found")
    return dashboard_data

@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(company: Company):
    """Create a new company (Admin/Senior only)"""
    # Check if company with same name exists
    existing = await Company.find_one(Company.name == company.name)
    if existing:
        raise HTTPException(status_code=400, detail="Company with this name already exists")
    
    await company.insert()
    return company

@router.post("/{company_id}/feedback")
async def upload_feedback(
    company_id: str, 
    files: List[UploadFile] = File(...),
    uploader_id: str = Form(...)
):
    print(f"\n[CRITICAL DEBUG] upload_feedback called for company: {company_id} with {len(files)} files")
    """Upload multiple interview feedback documents (Admin/Senior only)"""
    print(f"Received upload request: company_id={company_id}, uploader_id={uploader_id}, file_count={len(files)}")
    results = []
    company = await Company.get(company_id)
    company_name = company.name if company else ""
    
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in [".pdf", ".docx", ".doc"]:
            results.append({"file": file.filename, "status": "error", "message": "Unsupported format"})
            continue
        
        file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file.filename}")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create feedback record
            feedback = InterviewFeedback(
                company_id=company_id,
                uploader_id=uploader_id,
                file_name=file.filename,
                file_path=file_path,
                status="processing"
            )
            await feedback.insert()
            
            # Process text and update insights
            text = DocumentProcessor.extract_text(file_path)
            feedback.extracted_text = text
            feedback.status = "processed"
            await feedback.save()
            
            # Update/Create aggregated insights for the company using AI
            raw_insights = await DocumentProcessor.process_insights(text)
            
            try:
                with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"ROUTER: analyze_feedback finished. Tech Qs found: {len(raw_insights.get('technical_questions', []))}\n")
            except: pass
            
            current_insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
            
            try:
                with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"ROUTER: find_one finished. Found existing insights? {current_insights is not None}\n")
            except: pass

            if not current_insights:
                # Convert dict rounds to RoundDetail objects
                rounds_list = [
                    RoundDetail(
                        name=r["name"], 
                        description=r["description"],
                        difficulty=r.get("difficulty", "medium")
                    ) 
                    for r in raw_insights["rounds"]
                ]
                
                current_insights = CompanyInsights(
                    company_id=company_id,
                    rounds_summary=rounds_list,
                    insights=InsightMetadata(
                        frequently_asked_questions=raw_insights["faqs"],
                        important_technical_topics=raw_insights["topics"],
                        coding_difficulty=raw_insights["difficulty"],
                        common_mistakes=raw_insights["mistakes"],
                        preparation_tips=raw_insights["tips"],
                        technical_questions=raw_insights.get("technical_questions", [])
                    )
                )
                
                try:
                    with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"ROUTER: Creating NEW insights. Tech Qs: {len(current_insights.insights.technical_questions)}\n")
                except: pass
                
                await current_insights.insert()
                print(f"[DEBUG] Created new CompanyInsights with {len(rounds_list)} rounds")
            else:
                # Smarter Merge: Avoid redundancy using normalize logic
                from app.services.ai_service import AIService
                
                # PRIORITY 1: Merge Technical Questions
                try:
                    all_raw_qs = current_insights.insights.technical_questions + [
                        TechnicalQuestionDetail(**new_q) for new_q in raw_insights.get("technical_questions", [])
                    ]
                    
                    try:
                        with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"\nROUTER: STARTING Technical Question Merge. Current count: {len(current_insights.insights.technical_questions)}, New from PDF: {len(raw_insights.get('technical_questions', []))}\n")
                    except: pass

                    final_qs = []
                    seen_norm = set()
                    
                    # Broad keywords for the router cleanup phase
                    known_keywords = [
                        "Java", "Python", "SQL", "DBMS", "OS", "Operating System", "Data Structures", "Algorithms", "Networking", 
                        "C++", "React", "Node", "OOPS", "WebRTC", "API", "REST", "Frontend", "Backend", 
                        "Fullstack", "DNS", "AWS", "Docker", "Kubernetes", "Microservices", "Security", "Cloud", 
                        "Git", "CSS", "HTML", "Javascript", "Typescript", "Thread", "Process", "Deadlock", 
                        "Memory", "Cache", "Interface", "Abstract", "Class", "Inheritance", "Polymorphism", 
                        "Encapsulation", "Abstraction", "Exception", "Try", "Catch", "Finally", "Throw", 
                        "Collection", "List", "Map", "Set", "ArrayList", "LinkedList", "HashMap", "Stack", 
                        "Queue", "Recursion", "Complexity", "Big O", "Sorting", "Searching", "Graph", "Tree", 
                        "Binary", "Pointer", "Reference", "Given", "Constructor", "Destructor", "Static", "Final", 
                        "Access Modifier", "Overloading", "Overriding", "Lambda", "Stream", "Async", "Await", 
                        "Promise", "Component", "State", "Props", "Hook", "Database", "Index", "Join", "Query", 
                        "Transaction", "Normalisation", "Normalization"
                    ]
                    
                    for q in all_raw_qs:
                        q_text = q.question
                        norm = "".join(filter(str.isalnum, q_text.lower()))
                        if norm in seen_norm: continue
                        
                        has_topic = (q.topic and q.topic != "General Technical") or \
                                    any(kw.lower() in q_text.lower() for kw in known_keywords)
                                    
                        if AIService._is_valid_technical_question(q_text, has_topic):
                            final_qs.append(q)
                            seen_norm.add(norm)
                    
                    current_insights.insights.technical_questions = final_qs[:25] # Increased limit
                    
                    try:
                        with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"ROUTER: Technical Merge DONE. Final count: {len(current_insights.insights.technical_questions)}\n")
                    except: pass
                except Exception as e:
                    try:
                        with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"ROUTER ERROR in Tech Merge: {e}\n")
                    except: pass

                # PRIORITY 2: Merge other fields
                current_insights.insights.frequently_asked_questions = list(set(current_insights.insights.frequently_asked_questions + raw_insights["faqs"]))[:15]
                current_insights.insights.important_technical_topics = list(set(current_insights.insights.important_technical_topics + raw_insights["topics"]))[:15]
                current_insights.insights.common_mistakes = list(set(current_insights.insights.common_mistakes + raw_insights["mistakes"]))[:10]
                current_insights.insights.preparation_tips = list(set(current_insights.insights.preparation_tips + raw_insights["tips"]))[:10]

                # PRIORITY 3: Merge Rounds
                try:
                    new_structured_rounds = raw_insights.get("rounds", [])
                    
                    if new_structured_rounds:
                        # Map to consolidate rounds by name
                        round_map = {r.name: r.description for r in current_insights.rounds_summary}
                        for nr in new_structured_rounds:
                            # Only update if description is longer/better or it's a new round
                            if nr["name"] not in round_map or len(nr["description"]) > len(round_map[nr["name"]]):
                                round_map[nr["name"]] = nr["description"]
                        
                        # Rebuild summary
                        current_insights.rounds_summary = [
                            RoundDetail(name=name, description=desc) 
                            for name, desc in round_map.items()
                        ]
                except Exception as e:
                    print(f"ROUTER ERROR in Rounds Merge: {e}")

                current_insights.last_updated = datetime.utcnow()
                await current_insights.save()
                
            # NEW: Generate and save questions from feedback
            from app.services.ai_service import AIService
            generated_questions = await AIService.generate_questions_from_feedback(
                text,
                company_id,
                uploader_id,
                company_name=company_name,
                source="feedback"
            )
            await _save_generated_questions(
                generated_questions,
                company_id,
                uploader_id,
                company_name,
                source="feedback"
            )

            await CompanyService.update_company_from_feedback(company_id, raw_insights, text)
            
            results.append({"file": file.filename, "status": "success", "feedback_id": str(feedback.id)})
            
        except Exception as e:
            print(f"[ERROR] Failed to process {file.filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            try:
                feedback.status = "error"
                await feedback.save()
            except Exception:
                pass
            results.append({"file": file.filename, "status": "error", "message": str(e)})

    success_count = sum(1 for result in results if result["status"] == "success")
    error_count = len(results) - success_count

    if success_count == 0 and results:
        raise HTTPException(
            status_code=500,
            detail="All feedback files failed to process. Check backend logs for extraction errors."
        )

    if success_count > 0 and company:
        try:
            await _auto_enrich_company_questions(company, uploader_id)
        except Exception as exc:
            logger.warning("Company auto enrichment failed for %s: %s", company_id, exc)

    message = f"Processed {success_count} file(s)"
    if error_count:
        message += f", {error_count} failed"

    return {"message": message, "results": results}


@router.post("/{company_id}/sync-online")
async def sync_online_questions(
    company_id: str,
    payload: dict,
    current_user = Depends(get_current_user_from_token)
):
    """
    Sync questions from online URLs (GeeksforGeeks, etc.)
    """
    urls = payload.get("urls", [])
    if not urls:
        raise HTTPException(status_code=400, detail="At least one URL is required")

    company = await Company.get(company_id)
    company_name = company.name if company else ""
        
    all_extracted = []
    new_added = 0
    from app.services.ai_service import AIService
    
    for url in urls:
        try:
            questions = await AIService.extract_questions_from_url(
                url,
                company_id,
                str(current_user.id),
                company_name=company_name,
                source="web"
            )
            all_extracted.extend(questions)
            new_added += await _save_generated_questions(
                questions,
                company_id,
                str(current_user.id),
                company_name,
                source="web"
            )
        except Exception as e:
            print(f"Error syncing from {url}: {e}")
                
    return {
        "message": f"Sync complete. Found {len(all_extracted)} potential questions/topics. Added {new_added} new unique items to your bank." if all_extracted else "Sync complete, but no clear questions were detected in the content. Try a different URL or an 'Interview Experience' article.",
        "urls_processed": len(urls),
        "newly_added": new_added,
        "extracted_count": len(all_extracted)
    }
@router.post("/{company_id}/auto-sync")
async def auto_sync_questions(
    company_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Automatically discover and sync questions for a company"""
    from app.models.company import Company
    from app.models.assessment import Question
    from app.services.scraper_service import ScraperService
    from app.services.ai_service import AIService
    
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # 1. Discover Links
    urls = await ScraperService.discover_interview_links(company.name)
    if not urls:
        return {
            "message": f"Could not find any recent online interview experiences for {company.name} on GeeksforGeeks.",
            "extracted_count": 0,
            "newly_added": 0
        }
        
    # 2. Extract and Save
    total_extracted_qs = []
    newly_added = 0
    all_rounds_raw = []
    
    for url in urls:
        try:
            full_insights = await AIService.extract_full_insights_from_url(
                url,
                company_id,
                str(current_user.id),
                company_name=company.name
            )
            if not full_insights:
                continue
                
            # Questions
            questions_data = full_insights.get("generated_questions", [])
            newly_added += await _save_generated_questions(
                questions_data,
                company_id,
                str(current_user.id),
                company.name,
                source="web"
            )
            total_extracted_qs.extend(questions_data)

            # Rounds & Insights (New logic)
            all_rounds_raw.extend(full_insights.get("rounds", []))
            
        except Exception as e:
            print(f"Error auto-syncing from {url}: {e}")

        # 3. Aggregated Update for CompanyInsights
        if all_rounds_raw:
            current_insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
            
            # Map rounds by name for merging
            round_map = {}
            if current_insights:
                round_map = {r.name: r.description for r in current_insights.rounds_summary}
            
            for r in all_rounds_raw:
                r_name = r.get("name", "Interview Round")
                r_desc = r.get("description", "Interview round details extracted from online sources.")
                # Update if new round or better description
                if r_name not in round_map or len(r_desc) > len(round_map[r_name]):
                    round_map[r_name] = r_desc
            
            unique_rounds = [RoundDetail(name=n, description=d) for n, d in round_map.items()]
            
            # Collect other metadata from the last full_insights (if any)
            last_insights = full_insights if 'full_insights' in locals() else {}
            
            if not current_insights:
                current_insights = CompanyInsights(
                    company_id=company_id, 
                    rounds_summary=unique_rounds,
                    insights=InsightMetadata(
                        frequently_asked_questions=last_insights.get("faqs", []),
                        important_technical_topics=last_insights.get("topics", []),
                        common_mistakes=last_insights.get("mistakes", []),
                        preparation_tips=last_insights.get("tips", []),
                        coding_difficulty=last_insights.get("difficulty", "medium")
                    )
                )
                await current_insights.insert()
            else:
                current_insights.rounds_summary = unique_rounds
                
                # Merge metadata
                if last_insights:
                    current_insights.insights.frequently_asked_questions = list(set(current_insights.insights.frequently_asked_questions + last_insights.get("faqs", [])))[:15]
                    current_insights.insights.important_technical_topics = list(set(current_insights.insights.important_technical_topics + last_insights.get("topics", [])))[:15]
                    current_insights.insights.common_mistakes = list(set(current_insights.insights.common_mistakes + last_insights.get("mistakes", [])))[:10]
                    current_insights.insights.preparation_tips = list(set(current_insights.insights.preparation_tips + last_insights.get("tips", [])))[:10]
                    
                await current_insights.save()
            
    return {
        "message": f"Auto-discovery successful! Processed {len(urls)} sources and added {newly_added} new unique items for {company.name}. Interview rounds have been updated.",
        "newly_added": newly_added,
        "extracted_count": len(total_extracted_qs),
    }
