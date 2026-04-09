import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.ai_service import AIService
from app.services.scraper_service import ScraperService

async def debug_de_shaw_extraction():
    url = "https://www.geeksforgeeks.org/de-shaw-interview-experience-for-software-developer-internship-off-campus-aug-2021/"
    print(f"DEBUG: Processing {url}")
    
    content = await ScraperService.fetch_url_content(url)
    if not content:
        print("Failed to fetch content")
        return
        
    print(f"Content Length: {len(content)}")
    
    # 1. Test Round Extraction directly
    print("\n[TEST 1] Raw Round Extraction:")
    rounds = AIService._extract_and_normalize_rounds(content)
    print(f"Rounds Found: {len(rounds)}")
    for r in rounds:
        print(f"- {r['name']}: {r['description'][:100]}...")

    # 2. Test Full Insights
    print("\n[TEST 2] Full Insights Extraction:")
    insights = await AIService.analyze_feedback(content)
    print(f"Insights Keys: {insights.keys()}")
    print(f"Rounds in Insights: {len(insights.get('rounds', []))}")

if __name__ == "__main__":
    asyncio.run(debug_de_shaw_extraction())
