import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.ai_service import AIService
from app.models.assessment import QuestionType

async def test_extraction():
    test_text = """
    Interview Experience at Zoho:
    The interviewer asked me about my past roles.
    Question: What is your experience with handling high call volumes?
    They also asked a technical one:
    A) Stack B) Queue C) Array D) Tree
    Which data structure is LIFO? 
    """
    
    print("Testing question extraction...")
    questions = await AIService.generate_questions_from_feedback(test_text, "company_123", "user_123")
    
    for i, q in enumerate(questions):
        print(f"\nQuestion {i+1}: {q['text']}")
        print(f"Type: {q['type']}")
        print(f"Options: {q['options']}")
        
        if "call volumes" in q['text'].lower():
            # This should be behavioral or subjective, and have NO options
            assert q['type'] in ['behavioral', 'subjective']
            assert len(q['options']) == 0
            print("SUCCESS: Behavioral question correctly identified with no dummy options.")
            
        if "LIFO" in q['text']:
            # This should have real options extracted
            assert len(q['options']) >= 2
            assert "Stack" in q['options']
            print("SUCCESS: Technical MCQ correctly extracted real options from text.")

if __name__ == "__main__":
    asyncio.run(test_extraction())
