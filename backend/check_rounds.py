import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.company import Company, CompanyInsights
from app.config import settings
import traceback

async def check():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Company, CompanyInsights])
    
    # Try to find DE Shaw or display all companies and their rounds count
    companies = await Company.find_all().to_list()
    print(f"Total companies: {len(companies)}")
    for c in companies:
        insights = await CompanyInsights.find_one(CompanyInsights.company_id == str(c.id))
        rounds_count = len(insights.rounds_summary) if insights and insights.rounds_summary else 0
        print(f"Company: {c.name}, ID: {c.id}, Rounds: {rounds_count}")

if __name__ == "__main__":
    try:
        asyncio.run(check())
    except Exception as e:
        print("Error:")
        traceback.print_exc()
