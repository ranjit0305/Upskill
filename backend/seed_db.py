import asyncio
import motor.motor_asyncio
from beanie import init_beanie, Document
from pydantic import Field, BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv

# Re-defining models for simplicity in script or importing them
# Since we are in the same project, we can try to import, but for a standalone script, defining is safer

class QuestionType(str, Enum):
    APTITUDE = "aptitude"
    TECHNICAL = "technical"
    CODING = "coding"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Question(Document):
    type: QuestionType
    category: str
    difficulty: DifficultyLevel
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    tags: List[str] = []
    companies: List[str] = []
    test_cases: Optional[List[dict]] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "questions"

class Assessment(Document):
    title: str
    description: Optional[str] = None
    type: QuestionType
    questions: List[str]
    duration: int
    total_marks: int
    difficulty_level: DifficultyLevel
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "assessments"

async def seed_data():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "upskill_db")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    await init_beanie(database=client[database_name], document_models=[Question, Assessment])

    # Sample Questions
    questions_data = [
        {
            "type": QuestionType.APTITUDE,
            "category": "quant",
            "difficulty": DifficultyLevel.EASY,
            "question": "What is 15% of 200?",
            "options": ["20", "25", "30", "35"],
            "correct_answer": "30",
            "explanation": "15/100 * 200 = 30",
            "tags": ["percentage", "basic math"]
        },
        {
            "type": QuestionType.APTITUDE,
            "category": "logical",
            "difficulty": DifficultyLevel.MEDIUM,
            "question": "Complete the series: 2, 6, 12, 20, 30, ?",
            "options": ["40", "42", "44", "46"],
            "correct_answer": "42",
            "explanation": "The differences are 4, 6, 8, 10, 12. So 30 + 12 = 42.",
            "tags": ["series", "pattern"]
        },
        {
            "type": QuestionType.TECHNICAL,
            "category": "os",
            "difficulty": DifficultyLevel.EASY,
            "question": "Which of the following is not an operating system?",
            "options": ["Windows", "Linux", "Oracle", "macOS"],
            "correct_answer": "Oracle",
            "explanation": "Oracle is a database management system, not an operating system.",
            "tags": ["os basics"]
        }
    ]

    question_ids = []
    for q_data in questions_data:
        q = Question(**q_data)
        await q.insert()
        question_ids.append(str(q.id))

    # Sample Assessment
    assessment = Assessment(
        title="Sample Aptitude & Technical Test",
        description="A mixed test covering basic math, logic, and OS concepts.",
        type=QuestionType.APTITUDE,
        questions=question_ids,
        duration=10,
        total_marks=len(question_ids),
        difficulty_level=DifficultyLevel.EASY
    )
    await assessment.insert()

    print(f"Successfully seeded {len(questions_data)} questions and 1 assessment.")

if __name__ == "__main__":
    asyncio.run(seed_data())
