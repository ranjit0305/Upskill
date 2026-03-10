from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List, Optional
from app.models.company import Company, InterviewFeedback, CompanyInsights, InsightMetadata, RoundDetail, TechnicalQuestionDetail
from app.services.company_service import CompanyService
from app.services.document_processor import DocumentProcessor
from app.models.user import UserRole
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/companies", tags=["Companies"])

UPLOAD_DIR = "uploads/feedback"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

                # PRIORITY 3: Merge Rounds (Expensive)
                try:
                    try:
                        with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"ROUTER: Starting Rounds Merge (Slow path)...\n")
                    except: pass

                    current_rounds_text = "\n".join([f"{r.name}: {r.description}" for r in current_insights.rounds_summary])
                    combined_rounds_text = current_rounds_text + "\n" + text
                    new_structured_rounds = AIService._extract_and_normalize_rounds(combined_rounds_text)
                    
                    current_insights.rounds_summary = [
                        RoundDetail(name=r["name"], description=r["description"]) 
                        for r in new_structured_rounds
                    ]
                    
                    try:
                        with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"ROUTER: Rounds Merge DONE.\n")
                    except: pass
                except Exception as e:
                    try:
                        with open(r"d:\Upskill_github\Upskill\backend\absolute_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"ROUTER ERROR in Rounds Merge: {e}\n")
                    except: pass

                current_insights.last_updated = datetime.utcnow()
                await current_insights.save()
                
            # NEW: Generate and save questions from feedback
            from app.services.ai_service import AIService
            from app.models.assessment import Question
            generated_questions = await AIService.generate_questions_from_feedback(text, company_id, uploader_id)
            for q_data in generated_questions:
                # Check if question already exists
                existing_q = await Question.find_one(Question.question == q_data["text"])
                if not existing_q:
                    new_q = Question(
                        type=q_data["type"],
                        category=q_data["category"],
                        difficulty=q_data["difficulty"],
                        question=q_data["text"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data["explanation"],
                        companies=[company_id],
                        created_by=uploader_id
                    )
                    await new_q.insert()
                else:
                    # Just add company to existing question
                    if company_id not in existing_q.companies:
                        existing_q.companies.append(company_id)
                        await existing_q.save()
            
            results.append({"file": file.filename, "status": "success", "feedback_id": str(feedback.id)})
            
        except Exception as e:
            print(f"[ERROR] Failed to process {file.filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({"file": file.filename, "status": "error", "message": str(e)})
    
    return {"message": "Processing complete", "results": results}
