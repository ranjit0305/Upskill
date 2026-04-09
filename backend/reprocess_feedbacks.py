import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.company import Company, CompanyInsights, InterviewFeedback, RoundDetail
from app.config import settings
from app.services.ai_service import AIService
import traceback

async def reprocess():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Company, CompanyInsights, InterviewFeedback])
    
    companies = await Company.find_all().to_list()
    
    for c in companies:
        feedbacks = await InterviewFeedback.find(InterviewFeedback.company_id == str(c.id)).to_list()
        
        if feedbacks:
            insights = await CompanyInsights.find_one(CompanyInsights.company_id == str(c.id))
            if not insights:
                continue
                
            print(f"Reprocessing {c.name} with {len(feedbacks)} feedbacks")
            
            round_map = {r.name: r.description for r in insights.rounds_summary} if insights.rounds_summary else {}
            
            for fb in feedbacks:
                if not fb.extracted_text:
                    continue
                extracted_rounds = AIService._extract_and_normalize_rounds(fb.extracted_text)
                for nr in extracted_rounds:
                    if nr["name"] not in round_map or len(nr["description"]) > len(round_map[nr["name"]]):
                        round_map[nr["name"]] = nr["description"]
            
            if round_map:
                insights.rounds_summary = [
                    RoundDetail(name=n, description=d) for n, d in round_map.items()
                ]
                await insights.save()
                print(f"Updated {c.name} with {len(insights.rounds_summary)} rounds.")
            else:
                print(f"No rounds found for {c.name}.")

if __name__ == "__main__":
    try:
        asyncio.run(reprocess())
    except Exception as e:
        traceback.print_exc()
