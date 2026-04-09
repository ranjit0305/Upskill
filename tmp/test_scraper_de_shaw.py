import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.scraper_service import ScraperService

async def test_scraper_de_shaw():
    print("Testing Scraper for 'DE Shaw'...")
    urls = await ScraperService.discover_interview_links("DE Shaw")
    print(f"Found {len(urls)} URLs:")
    for url in urls:
        print(f"- {url}")

if __name__ == "__main__":
    asyncio.run(test_scraper_de_shaw())
