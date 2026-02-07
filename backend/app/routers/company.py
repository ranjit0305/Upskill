from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List, Optional
from app.models.company import Company, InterviewFeedback, CompanyInsights, InsightMetadata
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

@router.post("/{company_id}/feedback")
async def upload_feedback(
    company_id: str, 
    uploader_id: str = Form(...), 
    files: List[UploadFile] = File(...)
):
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
            
            current_insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
            if not current_insights:
                current_insights = CompanyInsights(
                    company_id=company_id,
                    rounds_summary=raw_insights["rounds"],
                    insights=InsightMetadata(
                        frequently_asked_questions=raw_insights["faqs"],
                        important_technical_topics=raw_insights["topics"],
                        coding_difficulty=raw_insights["difficulty"],
                        common_mistakes=raw_insights["mistakes"],
                        preparation_tips=raw_insights["tips"]
                    )
                )
                await current_insights.insert()
            else:
                # Smarter Merge: Avoid redundancy using normalize logic
                from app.services.ai_service import AIService
                from app.models.company import RoundDetail
                
                # Combine current and new rounds text for re-normalization
                current_rounds_text = "\n".join([f"{r.name}: {r.description}" for r in current_insights.rounds_summary])
                combined_rounds_text = current_rounds_text + "\n" + text
                
                new_structured_rounds = AIService._extract_and_normalize_rounds(combined_rounds_text)
                
                # Convert dict to RoundDetail models
                current_insights.rounds_summary = [
                    RoundDetail(name=r["name"], description=r["description"]) 
                    for r in new_structured_rounds
                ]
                
                # Merge lists with set deduplication
                current_insights.insights.frequently_asked_questions = list(set(current_insights.insights.frequently_asked_questions + raw_insights["faqs"]))[:15]
                current_insights.insights.important_technical_topics = list(set(current_insights.insights.important_technical_topics + raw_insights["topics"]))[:15]
                current_insights.insights.common_mistakes = list(set(current_insights.insights.common_mistakes + raw_insights["mistakes"]))[:10]
                current_insights.insights.preparation_tips = list(set(current_insights.insights.preparation_tips + raw_insights["tips"]))[:10]
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
            results.append({"file": file.filename, "status": "error", "message": str(e)})
    
    return {"message": "Processing complete", "results": results}
