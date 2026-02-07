import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import sys
import re

async def migrate_rounds():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "upskill_db")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]
    
    collection = db["company_insights"]
    async for insight in collection.find({}):
        rounds = insight.get("rounds_summary", [])
        if not rounds:
            continue
            
        # Check if already migrated (list of dicts)
        if len(rounds) > 0 and isinstance(rounds[0], dict):
            print(f"Company {insight.get('company_id')} already migrated.")
            continue
            
        # Migrate: convert simple names to {name, description}
        new_rounds = []
        for r in rounds:
            name = str(r)
            description = f"Preparation focused on {name} requirements."
            new_rounds.append({
                "name": name,
                "description": description,
                "difficulty": "medium"
            })
            
        await collection.update_one(
            {"_id": insight["_id"]},
            {"$set": {"rounds_summary": new_rounds}}
        )
        print(f"Migrated rounds for company {insight.get('company_id')}")

if __name__ == "__main__":
    asyncio.run(migrate_rounds())
