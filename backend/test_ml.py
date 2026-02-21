import asyncio
from app.services.ai_service import AIService
import logging

# Configure logging to see MLService output
logging.basicConfig(level=logging.INFO)

sample_text = """
My interview experience with Zoho:

Round 1: Online Assessment
It was a platform based test. 
Questions focus on aptitude and basic C programming.
There were questions on Profit and Loss, and some logical series.

Round 2: Technical Interview
I was asked to explain the difference between Process and Thread.
Then the interviewer asked me about my project on React.
He asked "What is Virtual DOM?".
It was quite challenging.

Round 3: HR Round
Basic behavior questions.
Tip: Be confident and honest.
"""

async def main():
    print("Running Analysis...")
    insights = await AIService.analyze_feedback(sample_text)
    
    print("\n--- Extracted Insights ---")
    print(f"Rounds found: {len(insights['rounds'])}")
    for r in insights['rounds']:
        print(f" - {r['name']}: {r['description']}")
    
    print(f"\nTopics: {insights['topics']}")
    print(f"Difficulty: {insights['difficulty']}")
    print(f"Mistakes: {insights['mistakes']}")
    print(f"Tips: {insights['tips']}")

if __name__ == "__main__":
    asyncio.run(main())
