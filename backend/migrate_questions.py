import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.assessment import Question, Assessment, Submission
from app.models.user import User
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.services.ai_service import AIService
from app.config import settings

async def update():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Question, Assessment, Submission, Company, CompanyInsights, InterviewFeedback]
    )
    
    questions = await Question.find({"type": "coding"}).to_list()
    bank = AIService.CODING_QUESTION_BANK
    
    updated_count = 0
    for q in questions:
        found = False
        for topic in bank:
            for temp in bank[topic]:
                if temp['description'] == q.question:
                    q.sample_input = temp.get('sample_input')
                    q.sample_output = temp.get('sample_output')
                    await q.save()
                    updated_count += 1
                    found = True
                    break
            if found: break
            
    print(f"Updated {updated_count} questions with sample data.")

if __name__ == "__main__":
    asyncio.run(update())
