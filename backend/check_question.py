import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.assessment import Question
from app.config import settings

async def check():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[Question]
    )
    
    # Search for the Two Sum question
    q = await Question.find_one({"question": {"$regex": "Given an array of integers nums"}})
    if q:
        print(f"Question found: {q.id}")
        print(f"Test Cases: {q.test_cases}")
        print(f"Sample Input: {q.sample_input}")
        print(f"Sample Output: {q.sample_output}")
    else:
        print("Question not found.")

if __name__ == "__main__":
    asyncio.run(check())
