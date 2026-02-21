import asyncio
from app.services.ai_service import AIService
import logging

logging.basicConfig(level=logging.ERROR)

# Doc 1: Standard numbering
text_1 = """
Round 1: Aptitude
Basic math.

Round 2: Coding
Two arrays question.

Round 3: Managerial
Discussed project and team fit.
"""

# Doc 2: Different naming for the same logical round (Round 3)
text_2 = """
Round 1: Aptitude
Math was easy.

Round 2: Coding
Tree traversal.

Managerial Round
Manager asked about my weakness and strength. (This is effectively Round 3)
"""

combined_text = text_1 + "\n\n" + text_2

async def main():
    print("--- Simulating Mismatched Naming Merge ---")
    insights = await AIService.analyze_feedback(combined_text)
    
    print(f"\nExtracted Rounds: {len(insights['rounds'])}")
    for i, r in enumerate(insights['rounds']):
        print(f"{i+1}. [{r['name']}]")
        print(f"   {r['description'][:50]}...")
        
    # We expect 3 rounds. If we see 4, "Managerial Round" failed to merge with "Round 3".
    if len(insights['rounds']) > 3:
        print("\n[!] FAIL: Redundant round detected (likely 'Managerial Round' separate from 'Round 3')")
    else:
        print("\n[+] PASS: Correctly merged")

if __name__ == "__main__":
    asyncio.run(main())
