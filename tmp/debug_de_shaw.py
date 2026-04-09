import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.company import Company, CompanyInsights
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def debug_insights_de_shaw():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Company, CompanyInsights])

    company_id = "69ce88848b1677b750612d1a"
    print(f"Checking insights for company ID: {company_id}")
    
    company = await Company.get(company_id)
    if company:
        print(f"Company: {company.name}")
    else:
        print("Company not found!")
        
    insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
    if insights:
        print(f"Insights found! Last Updated: {insights.last_updated}")
        print(f"Rounds Count: {len(insights.rounds_summary)}")
        for r in insights.rounds_summary:
            print(f"- {r.name}: {r.description[:50]}...")
            
        print("\nMetadata Check:")
        print(f"- FAQs: {len(insights.insights.frequently_asked_questions)}")
        print(f"- Mistakes: {len(insights.insights.common_mistakes)}")
        print(f"- Technical Questions: {len(insights.insights.technical_questions)}")
    else:
        print("NO CompanyInsights found for this company.")

if __name__ == "__main__":
    asyncio.run(debug_insights_de_shaw())
