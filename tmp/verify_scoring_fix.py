import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.assessment import Question, Submission, Answer, QuestionType, DifficultyLevel, Assessment
from app.models.performance import Performance, ReadinessScore
from app.services.assessment_service import AssessmentService
from app.schemas.assessment import SubmissionCreate, AnswerSubmit
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from bson import ObjectId

async def verify_fix():
    # Initialize DB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.upskill, document_models=[Question, Submission, Performance, ReadinessScore, Assessment])

    user_id = "test_user_refix"
    
    # 1. Create a mock question
    q = Question(
        type=QuestionType.TECHNICAL,
        category="General",
        difficulty=DifficultyLevel.EASY,
        question="What is 1+1?",
        correct_answer="2",
        explanation="Math"
    )
    await q.insert()
    
    # 2. Create a mock assessment referencing this question (as string ID)
    assessment = Assessment(
        title="Test Fix Assessment",
        type=QuestionType.TECHNICAL,
        questions=[str(q.id)],
        duration=10,
        total_marks=10,
        difficulty_level=DifficultyLevel.EASY
    )
    await assessment.insert()
    
    # 3. Simulate submission with overall time_taken
    submission_data = SubmissionCreate(
        assessment_id=str(assessment.id),
        answers=[
            AnswerSubmit(question_id=str(q.id), answer="2", time_taken=0)
        ],
        time_taken=120 # 2 minutes
    )
    
    print(f"Submitting with assessment_id={assessment.id}, qid={q.id}")
    submission = await AssessmentService.submit_assessment(user_id, submission_data)
    
    print(f"\nSubmission Score: {submission.score}%")
    print(f"Submission Accuracy: {submission.accuracy}%")
    print(f"Submission Time Taken: {submission.time_taken} seconds")
    
    assert submission.score == 100
    assert submission.time_taken == 120
    
    print("\nVerification Successful! The fix correctly handles string IDs and time_taken.")

if __name__ == "__main__":
    asyncio.run(verify_fix())
