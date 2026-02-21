import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.assessment import Question, Assessment, Submission
from app.models.user import User
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.services.assessment_service import AssessmentService
from app.config import settings

async def test_gen():
    try:
        # Initialize Beanie
        print("DEBUG: Initializing Beanie...", flush=True)
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[User, Question, Assessment, Submission, Company, CompanyInsights, InterviewFeedback]
        )

        company_id = "new_company_test_id"
        user_id = "test_user_id"
        
        print(f"DEBUG: Testing generation for company: {company_id}", flush=True)
        from app.services.ai_service import AIService
        print(f"DEBUG: Bank keys: {list(AIService.CODING_QUESTION_BANK.keys())}", flush=True)
        
        print("DEBUG: Calling create_company_coding_test...", flush=True)
        assessment = await AssessmentService.create_company_coding_test(company_id, user_id)
        print(f"DEBUG: Success! Assessment ID: {assessment.id}", flush=True)
        print(f"DEBUG: Questions: {len(assessment.questions)}", flush=True)
        
    except Exception as e:
        print(f"ERROR: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gen())
