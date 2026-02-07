import asyncio
from app.services.ai_service import AIService

async def test_gen():
    mock_text = """
    The Zoho interview started with an aptitude round. 
    It was quite challenging and covered topics like Profit and Loss, 
    Time and Work, and some questions on Trains (Speed Distance Time).
    
    In the second round, the interviewer asked: What is the difference between 
    a process and a thread? 
    They also asked me to explain the concept of indexing in DBMS.
    """
    
    print("Testing Question Generation...")
    questions = await AIService.generate_questions_from_feedback(
        mock_text, 
        "test_company_id", 
        "test_uploader_id"
    )
    
    print(f"Generated {len(questions)} questions:")
    for i, q in enumerate(questions):
        print(f"\n[{i+1}] Type: {q['type']}, Category: {q['category']}")
        print(f"Q: {q['text']}")
        print(f"Options: {q['options']}")
        print(f"Answer: {q['correct_answer']}")

if __name__ == "__main__":
    asyncio.run(test_gen())
