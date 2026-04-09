import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models.company import Company, CompanyInsights, RoundDetail

async def fill():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    from beanie import init_beanie
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Company, CompanyInsights])
    
    de_shaw = await Company.find_one(Company.name == "DE Shaw")
    if de_shaw:
        insights = await CompanyInsights.find_one(CompanyInsights.company_id == str(de_shaw.id))
        
        rounds = [
            RoundDetail(name="Round 1: Online Coding", description="The first round typically consists of 2-3 hard algorithmic challenges focusing on dynamic programming and graphs, hosted on HackerRank or a similar platform."),
            RoundDetail(name="Round 2: Technical Interview", description="Deep dive into data structures, system design, and core CS fundamentals (OS, DBMS, Networking)."),
            RoundDetail(name="Round 3: HR Interview", description="Behavioral questions, cultural fit assessment, and discussions about past projects and challenges.")
        ]
        
        if not insights:
            print("Creating new insights for DE Shaw")
            insights = CompanyInsights(company_id=str(de_shaw.id), rounds_summary=rounds)
            await insights.insert()
        else:
            print("Updating existing DE Shaw")
            insights.rounds_summary = rounds
            await insights.save()
        print("Success!")
        
if __name__ == "__main__":
    asyncio.run(fill())
