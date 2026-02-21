import asyncio
from app.services.ai_service import AIService
import logging

logging.basicConfig(level=logging.ERROR)

# Simulating two students submitting similar feedback for the same company
text_1 = """
Round 1: Online Test
The test consisted of 20 aptitude questions and 5 coding debugging questions.
It was easy.
"""

text_2 = """
Round 1: Aptitude
There were aptitude questions and some C code debugging.
Difficulty was easy level.
"""

combined_text = text_1 + "\n\n" + text_2

async def main():
    print("--- Simulating Feedback Merge ---")
    insights = await AIService.analyze_feedback(combined_text)
    
    print(f"\nExtracted Rounds: {len(insights['rounds'])}")
    for r in insights['rounds']:
        print(f"\n[{r['name']}]")
        print(f"Description: {r['description']}")
        
    # Check for repetition
    desc = insights['rounds'][0]['description']
    if "aptitude" in desc.lower() and desc.lower().count("aptitude") > 1:
        print("\n[!] DETECTED REPETITION / REDUNDANCY")
    else:
        print("\n[+] Looks clean")

if __name__ == "__main__":
    asyncio.run(main())
