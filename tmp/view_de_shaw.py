import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.scraper_service import ScraperService

async def view_de_shaw_text():
    url = "https://www.geeksforgeeks.org/de-shaw-interview-experience-for-software-developer-internship-off-campus-aug-2021/"
    content = await ScraperService.fetch_url_content(url)
    if content:
        print("--- CONTENT START ---")
        print(content[:2000])
        print("--- CONTENT END ---")

if __name__ == "__main__":
    asyncio.run(view_de_shaw_text())
