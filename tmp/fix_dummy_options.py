import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.assessment import Question, QuestionType
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def cleanup_dummy_options():
    # Initialize DB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Question])

    print("Searching for questions with dummy options ['A', 'B', 'C', 'D']...")
    
    # Target questions with exact dummy options
    cursor = Question.find({"options": ["A", "B", "C", "D"]})
    questions = await cursor.to_list()
    
    if not questions:
        print("No questions found with dummy options. Your database is clean!")
        return

    print(f"Found {len(questions)} questions to fix.")
    
    count = 0
    for q in questions:
        # Determine if it's behavioral or just subjective
        q_low = q.question.lower()
        is_behavioral = any(kw in q_low for kw in [
            "experience", "handling", "conflict", "team", "strength", "weakness", 
            "situation", "achieve", "success", "failure", "describe a time",
            "hobbies", "family", "salary", "vision", "goal", "accuracy",
            "ethics", "honesty", "pressure", "deadline", "conflict", "management",
            "introduce yourself", "why should we hire", "ambition", "career"
        ])
        
        # Update fields
        q.options = []
        if is_behavioral:
            q.type = QuestionType.BEHAVIORAL
        else:
            q.type = QuestionType.SUBJECTIVE
            
        # Ensure explanation is useful
        if "Directly extracted" in q.explanation or not q.explanation:
            q.explanation = "This is a situational question. Focus on providing a structured response using the STAR method (Situation, Task, Action, Result)."
        
        await q.save()
        count += 1
        print(f"Fixed [{q.type}]: {q.question[:50]}...")

    print(f"\nCleanup complete! Total fixed: {count}")

if __name__ == "__main__":
    asyncio.run(cleanup_dummy_options())
