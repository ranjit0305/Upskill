import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.company import Company
from app.models.assessment import Question
from app.services.scraper_service import ScraperService
from app.services.ai_service import AIService
import os

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill_db, document_models=[Company, Question])
    
    company_name = "Zoho"
    print(f"--- Discovering links for {company_name} ---")
    links = await ScraperService.discover_interview_links(company_name, limit=2)
    print(f"Found {len(links)} links: {links}")
    
    if not links:
        print("No links found. Checking search URL directly...")
        return

    print(f"\n--- Extracting from {links[0]} ---")
    # Using a dummy user ID
    questions = await AIService.extract_questions_from_url(links[0], "69875ce4f9f6c10cf300311a", "dummy_user_id")
    
    print(f"Extracted {len(questions)} questions.")
    for i, q in enumerate(questions[:3]):
        print(f"\nQ{i+1}: {q['text'][:100]}...")
        print(f"Type: {q['type']} | Category: {q['category']}")

if __name__ == "__main__":
    asyncio.run(main())
