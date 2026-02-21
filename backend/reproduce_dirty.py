import asyncio
from app.services.ai_service import AIService
import logging

logging.basicConfig(level=logging.ERROR)

# Simulating data from screenshots
text_clean = """
Round 2: Coding Assessment
Arrays, Recursion, Linked list.
"""

# Text with heavy noise (from screenshots)
text_dirty = """
Coding Round
Platform: Offline Round details: Face to Face Interview Areas covered: Recursion, Matrix, Trees
Your Comments: Same as above.
Questions on 3rd round: QUESTION DOMAIN QUESTION SOLUTION
Have you cleared the round : YES
"""

combined_text = text_clean + "\n\n" + text_dirty

async def main():
    print("--- Simulating Dirty Data Merge ---")
    insights = await AIService.analyze_feedback(combined_text)
    
    print(f"\nExtracted Rounds: {len(insights['rounds'])}")
    for r in insights['rounds']:
        print(f"\n[{r['name']}]")
        print(f"Description: {r['description'][:100]}...")
        
    # We want these to merge.
    # Expected: 1 Round (Round 2/Coding). 
    # Current likely result: 2 Rounds (Round 2 and Coding Round).
    if len(insights['rounds']) > 1:
        print("\n[!] FAIL: Failed to merge 'Coding Round' with 'Round 2' due to noise.")
    else:
        print("\n[+] PASS: Correctly merged")

if __name__ == "__main__":
    asyncio.run(main())
