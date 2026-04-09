import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.services.ai_service import AIService

async def debug_latest():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Company, CompanyInsights, InterviewFeedback])
    
    # Get latest feedback
    latest_fb = await InterviewFeedback.find_one({}, sort=[("_id", -1)])
    if not latest_fb:
        print("No feedback found")
        return
        
    print(f"Latest Feedback: {latest_fb.file_name}")
    text = getattr(latest_fb, 'extracted_text', '')
    print(f"Text length: {len(text)}")
    print("--- First 500 chars :")
    print(text[:500])
    print("---")
    
    rounds = AIService._extract_and_normalize_rounds(text)
    print(f"Extracted Rounds: {len(rounds)}")
    for r in rounds:
        print(f" - {r['name']}: {r['description']}")

if __name__ == "__main__":
    asyncio.run(debug_latest())
