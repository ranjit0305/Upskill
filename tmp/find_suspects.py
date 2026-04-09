import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.assessment import Question
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def find_suspects():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Question])

    print("Checking for behavioral questions with MCQ options...")
    
    # Let's find some questions by keyword
    cursor = Question.find({"question": {"$regex": "accuracy", "$options": "i"}})
    questions = await cursor.to_list()
    
    for q in questions:
        print(f"\nFound Q: {q.question[:60]}...")
        print(f"Type: {q.type}")
        print(f"Options: {q.options}")
        print(f"IDs: {q.id}")

if __name__ == "__main__":
    asyncio.run(find_suspects())
