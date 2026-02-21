import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.assessment import Question, Assessment, Submission, QuestionType
from app.models.user import User
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.config import settings

async def inspect():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Question, Assessment, Submission, Company, CompanyInsights, InterviewFeedback]
    )

    assessments = await Assessment.find().to_list()
    print(f"Total Assessments: {len(assessments)}")
    for a in assessments:
        print(f"  Assessment {a.id}: type={a.type}, questions_type={type(a.questions)}")
        if isinstance(a.questions, str):
            print(f"    WARNING: questions field is a string for assessment {a.id}")
    
    coding_qs = await Question.find({"type": QuestionType.CODING}).to_list()
    print(f"Coding Questions (Enum): {len(coding_qs)}")
    
    coding_qs_str = await Question.find({"type": "coding"}).to_list()
    print(f"Coding Questions (String): {len(coding_qs_str)}")

    from app.services.ai_service import AIService
    print(f"Bank topics: {list(AIService.CODING_QUESTION_BANK.keys())}")
    for topic, qs in AIService.CODING_QUESTION_BANK.items():
        print(f"  {topic}: {len(qs)} questions")

if __name__ == "__main__":
    asyncio.run(inspect())
