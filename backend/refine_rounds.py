import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import sys

# Add the current directory to path so we can import apps
sys.path.append(os.getcwd())

async def refine_rounds():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "upskill_db")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]
    
    # We need the AI Service logic
    from app.services.ai_service import AIService
    
    collection = db["company_insights"]
    async for insight in collection.find({}):
        rounds = insight.get("rounds_summary", [])
        if not rounds:
            continue
            
        # Combine rounds into a text for normalization
        rounds_text = "\n".join(rounds)
        new_rounds = AIService._extract_and_normalize_rounds(rounds_text)
        
        if new_rounds != rounds:
            await collection.update_one(
                {"_id": insight["_id"]},
                {"$set": {"rounds_summary": new_rounds}}
            )
            print(f"Refined rounds for company {insight.get('company_id')}: {rounds} -> {new_rounds}")
        else:
            print(f"Rounds for company {insight.get('company_id')} are already clean.")

if __name__ == "__main__":
    asyncio.run(refine_rounds())
