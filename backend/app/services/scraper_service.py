import httpx
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class ScraperService:
    """Service to fetch and parse interview content from online sources"""
    
    @staticmethod
    async def fetch_url_content(url: str) -> Optional[str]:
        """Fetch raw HTML and extract main text content"""
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Detect blockers and 404s in the text content
                raw_text = soup.get_text().lower()
                if any(x in raw_text for x in ["404", "page not found", "access denied", "blocked", "security check", "robot check"]):
                    logger.warning(f"Likely blocked or 404 at {url}")
                    return None
                
                # Specialized parsing for common sites
                content = ""
                if "geeksforgeeks.org" in url:
                    content_div = soup.find("div", class_="content") or soup.find("article")
                    if content_div:
                        content = content_div.get_text(separator='\n', strip=True)
                
                if not content:
                    content = soup.get_text(separator='\n', strip=True)
                
                # Final check for minimal meaningful content
                if len(content) < 500 and "interview" not in content.lower():
                    logger.warning(f"Content from {url} is too short or irrelevant ({len(content)} chars)")
                    return None

                return content
                
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

    @staticmethod
    async def discover_interview_links(company_name: str, limit: int = 3) -> List[str]:
        """Automatically find interview experience links for a company using GFG search"""
        search_url = f"https://www.geeksforgeeks.org/search/{company_name.replace(' ', '+')}+Interview+Experience/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                response = await client.get(search_url, headers=headers)
                if response.status_code != 200:
                    return []
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                links = []
                
                # Look for links in article tags (typical GFG search results)
                for article in soup.find_all('article'):
                    a = article.find('a', href=True)
                    if a and 'interview' in a['href'].lower():
                        links.append(a['href'])
                
                # Fallback to any relevant link on the page
                if len(links) < limit:
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if 'interview-experience' in href.lower() and company_name.lower() in href.lower():
                            if href.startswith('http') and href not in links:
                                links.append(href)
                
                return list(set(links))[:limit]
        except Exception as e:
            logger.error(f"Error discovering links for {company_name}: {e}")
            return []
