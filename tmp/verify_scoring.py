import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.assessment import Question, Submission, Answer, QuestionType, DifficultyLevel, Assessment
from app.models.performance import Performance, ReadinessScore
from app.services.performance_service import PerformanceService
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def verify():
    # Initialize DB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Question, Submission, Performance, ReadinessScore, Assessment])

    user_id = "test_user_123"
    
    # 1. Clear previous test data
    await Performance.find(Performance.user_id == user_id).delete()
    await ReadinessScore.find(ReadinessScore.user_id == user_id).delete()
    await Submission.find(Submission.user_id == user_id).delete()
    
    # 2. Create mock questions for different topics
    q1 = Question(
        type=QuestionType.TECHNICAL,
        category="Operating Systems",
        difficulty=DifficultyLevel.EASY,
        question="What is a process?",
        correct_answer="Program in execution",
        explanation="..."
    )
    await q1.insert()
    
    q2 = Question(
        type=QuestionType.TECHNICAL,
        category="DBMS",
        difficulty=DifficultyLevel.EASY,
        question="What is SQL?",
        correct_answer="Structured Query Language",
        explanation="..."
    )
    await q2.insert()
    
    # 3. Create a mock submission
    # User gets OS right, but DBMS wrong
    submission = Submission(
        user_id=user_id,
        assessment_id="test_assessment",
        answers=[
            Answer(question_id=str(q1.id), is_correct=True),
            Answer(question_id=str(q1.id), is_correct=True), # 2 correct in OS
            Answer(question_id=str(q1.id), is_correct=True), # 3 correct in OS (meets the 3 total questions threshold)
            Answer(question_id=str(q2.id), is_correct=False),
            Answer(question_id=str(q2.id), is_correct=False),
            Answer(question_id=str(q2.id), is_correct=False), # 3 incorrect in DBMS
        ],
        score=50,
        accuracy=50,
        submitted_at=datetime.utcnow()
    )
    await submission.insert()
    
    # 4. Trigger performance update
    print("Updating performance...")
    await PerformanceService.update_performance(user_id, submission)
    
    # 5. Calculate readiness score
    print("Calculating readiness score...")
    readiness = await PerformanceService.calculate_readiness_score(user_id)
    
    # 6. Verify results
    performance = await Performance.find_one(Performance.user_id == user_id)
    print(f"\nWeak Topics: {performance.weak_topics}")
    print(f"Strong Topics: {performance.strong_topics}")
    print(f"Recommendations: {readiness.recommendations}")
    
    assert "DBMS" in performance.weak_topics or "dbms" in [t.lower() for t in performance.weak_topics]
    assert "Operating Systems" in performance.strong_topics or "operating systems" in [t.lower() for t in performance.strong_topics]
    
    # Check if recommendations contain the weak topic
    has_dbms_rec = any("DBMS" in rec for rec in readiness.recommendations)
    print(f"Found DBMS recommendation: {has_dbms_rec}")
    
    print("\nVerification Successful!")

if __name__ == "__main__":
    asyncio.run(verify())
