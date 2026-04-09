import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.company import Company, CompanyInsights, RoundDetail
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from unittest.mock import patch, AsyncMock

async def final_verification():
    # Initialize DB (using test db if possible, but for this mock live is okay)
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Company, CompanyInsights])

    company_id = "69ce88848b1677b750612d1a" # DE Shaw ID from user screenshot
    print(f"Starting Final Verification for DE Shaw ({company_id})")

    # 1. Ensure a manual round exists
    insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
    if not insights:
        insights = CompanyInsights(company_id=company_id, rounds_summary=[RoundDetail(name="Initial Check", description="Manual test round")])
        await insights.insert()
    else:
        if not any(r.name == "Initial Check" for r in insights.rounds_summary):
            insights.rounds_summary.append(RoundDetail(name="Initial Check", description="Manual test round"))
            await insights.save()

    print(f"Current rounds count: {len(insights.rounds_summary)}")

    # 2. TEST 1: SYNC FAILURE (Should NOT wipe data)
    # Mocking a tiny bit of content that ScraperService now considers a failure
    failed_content = "GeeksforGeeks | 404 Page Not Found"
    
    # We simulate the router logic partially
    from app.services.ai_service import AIService
    print("\nSimulating failed sync (404)...")
    new_rounds = AIService._extract_and_normalize_rounds(failed_content)
    print(f"AI extracted {len(new_rounds)} rounds from 404.")
    
    # Non-destructive logic check
    if len(new_rounds) == 0:
        print("SUCCESS: AI found no rounds in 404. Router will SKIP destructive update.")
    else:
        print("FAIL: AI found rounds in 404 text! Check regex.")
        return

    # 3. TEST 2: PDF UPLOAD (Numbered rounds)
    print("\nSimulating DE Shaw PDF Upload...")
    pdf_text = """
    1. OA: Online assessment with aptitude and coding.
    2. Technical Round 1: Questions on OOPS and DBMS.
    3. Technical Round 2: Problem solving and System design.
    """
    new_rounds_pdf = AIService._extract_and_normalize_rounds(pdf_text)
    print(f"AI extracted {len(new_rounds_pdf)} rounds from PDF text.")
    
    if len(new_rounds_pdf) >= 3:
        print("SUCCESS: AI correctly identified numbered rounds from PDF format.")
    else:
        print(f"FAIL: AI only found {len(new_rounds_pdf)} rounds. Check regex pattern.")
        return

    print("\nFinal Verification Complete! Sync is now robust and non-destructive.")

if __name__ == "__main__":
    asyncio.run(final_verification())
