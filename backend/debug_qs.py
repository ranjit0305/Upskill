import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv

async def check_qs():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "upskill_db")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]
    
    company_id = "698045dfbec872713466d484" # Zoho
    
    # 1. Check all questions for Zoho
    all_qs = await db["questions"].find({"companies": company_id}).to_list(100)
    print(f"Total questions for Zoho: {len(all_qs)}")
    
    # 2. Check aptitude specific
    apt_qs = await db["questions"].find({"companies": company_id, "type": "aptitude"}).to_list(100)
    print(f"Aptitude questions for Zoho: {len(apt_qs)}")
    for q in apt_qs:
        print(f"- {q['question']}")

    # 3. Check technical specific
    tech_qs = await db["questions"].find({"companies": company_id, "type": "technical"}).to_list(100)
    print(f"Technical questions for Zoho: {len(tech_qs)}")

if __name__ == "__main__":
    asyncio.run(check_qs())
