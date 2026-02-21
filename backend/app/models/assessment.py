from beanie import Document, Link
from pydantic import Field, BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    """Question type enumeration"""
    APTITUDE = "aptitude"
    TECHNICAL = "technical"
    CODING = "coding"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(Document):
    """Question model for all question types"""
    
    type: QuestionType
    category: str  # "quant", "logical", "verbal", "os", "dbms", "cn", etc.
    difficulty: DifficultyLevel
    question: str
    options: Optional[List[str]] = None  # For MCQs
    correct_answer: str
    explanation: str
    tags: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    test_cases: Optional[List[dict]] = None  # For coding questions
    sample_input: Optional[str] = None
    sample_output: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_generated: bool = False
    
    class Settings:
        name = "questions"
        indexes = [
            "type",
            "category",
            "difficulty",
            "tags",
        ]


class Assessment(Document):
    """Assessment/Test model"""
    
    title: str
    description: Optional[str] = None
    type: QuestionType
    questions: List[str] = Field(default_factory=list)  # Question IDs
    duration: int  # in minutes
    total_marks: int
    difficulty_level: DifficultyLevel
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_generated: bool = False
    
    class Settings:
        name = "assessments"
        indexes = [
            "type",
            "difficulty_level",
        ]


class Answer(BaseModel):
    """Individual answer model"""
    question_id: str
    answer: Optional[str] = None  # For MCQs/Text
    code: Optional[str] = None    # For Coding
    language: Optional[str] = None # For Coding
    is_correct: bool = False
    time_taken: int = 0  # in seconds
    test_results: Optional[List[dict]] = None # For Coding


class Submission(Document):
    """Submission model for test attempts"""
    
    user_id: str
    assessment_id: str
    answers: List[Answer]
    score: float = 0.0
    accuracy: float = 0.0
    time_taken: int = 0  # in seconds
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    coding_score: float = 0.0  # Separate coding score
    total_score: float = 0.0   # Combined score
    
    class Settings:
        name = "submissions"
        indexes = [
            "user_id",
            "assessment_id",
            "submitted_at",
        ]
