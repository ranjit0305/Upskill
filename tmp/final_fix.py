import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.assessment import Question, QuestionType
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def find_problematic_questions():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Question])

    print("Checking all generated questions for dummy options...")
    
    # Let's find ALL questions and inspect them
    cursor = Question.find_all()
    questions = await cursor.to_list()
    
    found_count = 0
    for q in questions:
        # Check if options contain just single letters or placeholders
        options = q.options or []
        is_dummy = (
            len(options) == 4 and 
            all(len(str(o).strip()) == 1 for o in options)
        ) or (
            len(options) == 4 and
            options[0].strip().upper() == "A" and
            options[1].strip().upper() == "B"
        )
        
        if is_dummy:
            print(f"\nFOUND DUMMY Q: {q.question[:60]}...")
            print(f"Options: {options}")
            print(f"ID: {q.id}")
            found_count += 1
            
            # Now let's fix it!
            # Use improved detection
            q_low = q.question.lower()
            is_behavioral = any(kw in q_low for kw in [
                "experience", "handling", "conflict", "team", "strength", "weakness", 
                "situation", "achieve", "success", "failure", "describe a time",
                "hobbies", "family", "salary", "vision", "goal", "accuracy",
                "ethics", "honesty", "pressure", "deadline", "management"
            ])
            
            q.options = []
            if is_behavioral:
                q.type = QuestionType.BEHAVIORAL
            else:
                q.type = QuestionType.SUBJECTIVE
                
            q.explanation = "This is a situational question. Focus on providing a structured response using the STAR method."
            await q.save()
            print(f"FIXED -> Type: {q.type}")

    print(f"\nScan complete. Fixed {found_count} questions.")

if __name__ == "__main__":
    asyncio.run(find_problematic_questions())
