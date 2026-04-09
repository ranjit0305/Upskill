import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.company import Company, CompanyInsights, InterviewFeedback, RoundDetail
from app.services.ai_service import AIService
import traceback

async def test_merge():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Company, CompanyInsights, InterviewFeedback])
    
    # Get latest feedback
    latest_fb = await InterviewFeedback.find_one({}, sort=[("_id", -1)])
    if not latest_fb:
        print("No feedback found")
        return
        
    text = getattr(latest_fb, 'extracted_text', '')
    
    # Simulate DocumentProcessor.process_insights
    raw_insights = {"rounds": AIService._extract_and_normalize_rounds(text)}
    
    # Simulate current_insights
    # Since DE Shaw is Company 3, let's just make a dummy current_insights
    current_insights = CompanyInsights(company_id="dummy", rounds_summary=[])
    
    try:
        new_structured_rounds = raw_insights.get("rounds", [])
        print(f"New structured rounds: {new_structured_rounds}")
        
        if new_structured_rounds:
            # Map to consolidate rounds by name
            round_map = {r.name: r.description for r in current_insights.rounds_summary}
            for nr in new_structured_rounds:
                # Only update if description is longer/better or it's a new round
                if nr["name"] not in round_map or len(nr["description"]) > len(round_map.get(nr["name"], "")):
                    round_map[nr["name"]] = nr["description"]
            
            # Rebuild summary
            current_insights.rounds_summary = [
                RoundDetail(name=name, description=desc) 
                for name, desc in round_map.items()
            ]
            print(f"Success! Updated rounds: {current_insights.rounds_summary}")
    except Exception as e:
        print(f"ROUTER ERROR in Rounds Merge: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_merge())
