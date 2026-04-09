import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.company import Company
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def list_all_companies():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Company])

    print("Listing all companies in database...")
    cursor = Company.find_all()
    companies = await cursor.to_list()
    
    for c in companies:
        print(f"ID: {c.id} | Name: {c.name}")

if __name__ == "__main__":
    asyncio.run(list_all_companies())
