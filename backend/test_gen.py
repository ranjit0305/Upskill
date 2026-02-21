import requests
import json

BASE_URL = "http://localhost:8000"

# Assuming we can get a token or the endpoint is open in dev
# (Already logged in in the browser, but here we need a token)
# Let's try to find an existing user to get a token

def test_generation():
    # Attempt to login or use a known dev user
    # For dev, maybe we can skip auth or use a test account
    # But since I can't easily get the password, I'll just check the code again.
    pass

if __name__ == "__main__":
    print("Checking AssessmentService logic via script...")
    # I'll run the service logic directly in a script to see where it fails
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    import sys
    import os

    sys.path.append(os.getcwd())
    from app.models.assessment import Question, Assessment, QuestionType, DifficultyLevel
    from app.models.company import Company, CompanyInsights
    from app.services.assessment_service import AssessmentService

    async def run_test():
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        database = client.upskill
        await init_beanie(database=database, document_models=[Question, Assessment, Company, CompanyInsights])
        
        company_id = "69877c0f3653cb7fbc068803"
        user_id = "69877c0f3653cb7fbc068802" # Mock user ID
        
        try:
            print(f"Generating test for company {company_id}...")
            assessment = await AssessmentService.create_company_aptitude_test(company_id, user_id)
            print(f"Success! Assessment ID: {assessment.id}")
            print(f"Question count: {len(assessment.questions)}")
        except Exception as e:
            print(f"Error during generation: {e}")
            import traceback
            traceback.print_exc()
        
        await client.close()

    asyncio.run(run_test())
