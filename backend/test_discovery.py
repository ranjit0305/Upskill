import httpx
from bs4 import BeautifulSoup
import re

async def discover_links(company_name: str):
    # Using the refined search pattern found in the HTML metadata
    search_url = f"https://www.geeksforgeeks.org/search/{company_name.replace(' ', '+')}+Interview+Experience/"
    print(f"Searching: {search_url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        response = await client.get(search_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to search: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        with open("discovery_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"DEBUG: Saved HTML to discovery_debug.html")
        
        # Try a more specific GFG search result pattern
        # Usually it's in <a> tags inside <article>
        for article in soup.find_all('article'):
            a = article.find('a', href=True)
            if a and 'interview' in a['href'].lower():
                links.append(a['href'])
        
        # Fallback to any link
        if not links:
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'interview-experience' in href.lower() and company_name.lower() in href.lower():
                    links.append(href)
                    
        return list(set(links))[:5]

import asyncio
if __name__ == "__main__":
    links = asyncio.run(discover_links("Zoho"))
    print(f"Found {len(links)} links:")
    for l in links:
        print(f" - {l}")
