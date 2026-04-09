import asyncio
from app.services.ai_service import AIService
import traceback

sample_feedback = """
We had 3 rounds for DE Shaw.
Round 1: Online Assessment containing Aptitude questions and 2 coding questions. It was somewhat difficult.
Round 2: Technical Interview. They asked me questions on Java, OOPs concepts, and SQL queries.
Round 3: HR Interview. Basic cultural fit questions, salary expectations, and willingness to relocate.
"""

async def run_test():
    try:
        print("Starting analyze")
        insights = await AIService.analyze_feedback(sample_feedback)
        print(f"Rounds extracted: {len(insights.get('rounds', []))}")
        for r in insights.get('rounds', []):
            print(f"- {r['name']}: {r['description']}")
    except Exception as e:
        print("Error:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
