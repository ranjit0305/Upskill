import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    dbs = await client.list_database_names()
    print(f"Databases: {dbs}")
    
    if "upskill" in dbs:
        db = client.upskill
        collections = await db.list_collection_names()
        print(f"Collections in 'upskill': {collections}")
        
        # Check counts
        if "questions" in collections:
            count = await db.questions.count_documents({})
            print(f"Total questions: {count}")
            
            # Find a few and print them
            q = await db.questions.find_one()
            if q:
                print(f"Sample Question: {q}")

if __name__ == "__main__":
    asyncio.run(check_db())
