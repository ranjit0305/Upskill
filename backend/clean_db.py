import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.assessment import Assessment, Question, Submission
from app.models.user import User
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.config import settings

async def clean():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Question, Assessment, Submission, Company, CompanyInsights, InterviewFeedback]
    )
    # Delete all coding assessments that were generated
    await Assessment.find({"type": "coding", "is_generated": True}).delete()
    print("Cleaned all generated coding assessments.")

if __name__ == "__main__":
    asyncio.run(clean())
