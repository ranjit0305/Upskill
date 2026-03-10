import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check_db():
    # Try to get mongo uri from env or default
    mongo_uri = "mongodb://localhost:27017" # common default
    # But let's check settings if possible. Assuming local mongo for now as per start.bat
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client["upskill"] # assuming db name from context
    
    company_id = "6999ddda05dccabeb542db93"
    
    insights = await db["company_insights"].find_one({"company_id": company_id})
    
    if not insights:
        print(f"No insights found for company {company_id}")
        return

    tech_qs = insights.get("insights", {}).get("technical_questions", [])
    print(f"Found {len(tech_qs)} technical questions in DB for company {company_id}:")
    for q in tech_qs:
        print(f"- [{q.get('topic')}] {q.get('question')}")

if __name__ == "__main__":
    asyncio.run(check_db())
