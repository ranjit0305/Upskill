import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.company import Company, CompanyInsights, InterviewFeedback

async def c():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Company, CompanyInsights, InterviewFeedback])
    
    de_shaw = await Company.find_one({"name": "DE Shaw"})
    if not de_shaw:
        print("No DE Shaw company")
        return
        
    print(de_shaw.id)
    insights = await CompanyInsights.find_one({"company_id": str(de_shaw.id)})
    if not insights:
        print("No insights")
        return
        
    print("Rounds summary count:", len(insights.rounds_summary))
    for r in insights.rounds_summary:
        print("-", r.name, len(r.description))

if __name__ == "__main__":
    asyncio.run(c())
