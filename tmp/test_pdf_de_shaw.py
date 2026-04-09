import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.ai_service import AIService

async def test_pdf_extraction_de_shaw():
    mock_pdf_text = """
    DE Shaw Interview Experience
    1. Online Assessment: The first round was an OA. It had 20 MCQs on OS, DBMS, and Aptitude. 
    There were 2 coding questions on recursion and dynamic programming.
    2. Technical Interview 1: They asked about my resume projects and deep dived into OOPS concepts.
    3. Technical Interview 2: This round was mostly on System Design and Puzzles.
    4. HR Round: Discussion about salary and relocation.
    """
    
    print("Testing round extraction from mock PDF...")
    rounds = AIService._extract_and_normalize_rounds(mock_pdf_text)
    
    print(f"Rounds Found: {len(rounds)}")
    for r in rounds:
        print(f" - {r['name']}: {r['description'][:100]}...")
    
    assert len(rounds) >= 3
    print("\nSUCCESS: PDF Round extraction is working with the new regex!")

if __name__ == "__main__":
    asyncio.run(test_pdf_extraction_de_shaw())
