import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import sys
from datetime import datetime

# Add the current directory to path so we can import apps
sys.path.append(os.getcwd())

async def cleanup_zoho_ultra():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "upskill_db")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]
    
    from app.services.ai_service import AIService
    
    # Get Zoho documents
    company_id = "698045dfbec872713466d484" # Zoho ID from your screenshots
    fb_docs = await db["interview_feedback"].find({"company_id": company_id}).to_list(100)
    all_text = "\n\n".join([doc.get("extracted_text", "") for doc in fb_docs if doc.get("extracted_text")])
    
    if not all_text:
        print("No feedback text found to extract from.")
        return
        
    print(f"Extracting and cleaning rounds from {len(fb_docs)} documents using ultra-logic...")
    refined_rounds = AIService._extract_and_normalize_rounds(all_text)
    
    # Update CompanyInsights
    await db["company_insights"].update_one(
        {"company_id": company_id},
        {"$set": {
            "rounds_summary": refined_rounds,
            "last_updated": datetime.utcnow()
        }}
    )
    print(f"Successfully refined {len(refined_rounds)} rounds.")
    for r in refined_rounds:
        print(f"\n- {r['name']}")
        print(f"  {r['description'][:150]}...")

if __name__ == "__main__":
    asyncio.run(cleanup_zoho_ultra())
