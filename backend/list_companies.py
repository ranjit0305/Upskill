import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.company import Company
from app.models.assessment import Question
import os

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill_db, document_models=[Company, Question])
    
    companies = await Company.find_all().to_list()
    for c in companies:
        print(f"ID: {c.id} | Name: {c.name}")

if __name__ == "__main__":
    asyncio.run(main())
