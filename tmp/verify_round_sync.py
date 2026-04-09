import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.company import Company, CompanyInsights
from app.models.user import User
from app.services.ai_service import AIService
from app.services.scraper_service import ScraperService
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from unittest.mock import patch, AsyncMock

async def verify_round_sync():
    # Initialize DB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Company, CompanyInsights, User])

    # 1. Create a test company
    company_name = "SyncTestCorp"
    company = await Company.find_one(Company.name == company_name)
    if not company:
        company = Company(name=company_name, description="Testing sync")
        await company.insert()
    
    company_id = str(company.id)
    print(f"Testing for company: {company_name} ({company_id})")

    # 2. Mock online content
    mock_url = "https://example.com/sync-test"
    mock_content = """
    Interview Experience at SyncTestCorp:
    Round 1: First Round was an Online Assessment. It had 20 aptitude questions.
    Round 2: Technical Interview. They asked about Java and SQL.
    Questions: What is a deadlock? Explain Joins.
    """

    # 3. Trigger manual extraction (simulating what auto_sync does internaly)
    with patch('app.services.scraper_service.ScraperService.fetch_url_content', AsyncMock(return_value=mock_content)):
        print(f"Extracting insights from mocked URL...")
        insights = await AIService.extract_full_insights_from_url(mock_url, company_id, "test_user")
        
        print(f"Rounds found: {[r['name'] for r in insights.get('rounds', [])]}")
        assert len(insights.get('rounds', [])) >= 2
        
        # 4. Save to DB (simulating the router logic)
        all_rounds_raw = insights.get('rounds', [])
        unique_rounds = []
        from app.models.company import RoundDetail, InsightMetadata
        seen_rounds = set()
        for r in all_rounds_raw:
            r_name = r.get("name", "Interview Round")
            if r_name not in seen_rounds:
                unique_rounds.append(RoundDetail(
                    name=r_name, 
                    description=r.get("description", "Extracted description")
                ))
                seen_rounds.add(r_name)
        
        current_insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
        if not current_insights:
            current_insights = CompanyInsights(
                company_id=company_id, 
                rounds_summary=unique_rounds,
                insights=InsightMetadata()
            )
            await current_insights.insert()
        else:
            current_insights.rounds_summary = unique_rounds
            await current_insights.save()
            
        # 5. Final check
        refreshed = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
        print(f"DB Check: Rounds in CompanyInsights: {len(refreshed.rounds_summary)}")
        assert len(refreshed.rounds_summary) >= 2
        print("\nVerification Successful! Interview rounds are now correctly synced from online sources.")

if __name__ == "__main__":
    asyncio.run(verify_round_sync())
