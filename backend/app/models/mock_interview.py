from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MockInterviewMode(str, Enum):
    GENERAL = "general"
    COMPANY = "company"


class MockInterviewStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MockQuestionCategory(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"
    CODING = "coding"


class MockInterviewQuestion(BaseModel):
    category: MockQuestionCategory
    prompt: str
    topic: Optional[str] = None
    expected_points: List[str] = Field(default_factory=list)
    source: str = "general"
    difficulty: str = "medium"


class MockInterviewFeedback(BaseModel):
    relevance: float = 0.0
    clarity: float = 0.0
    structure: float = 0.0
    technical_accuracy: float = 0.0
    confidence: float = 0.0
    score: float = 0.0
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    suggested_answer: str = ""


class MockInterviewAnswer(BaseModel):
    question_index: int
    category: MockQuestionCategory
    prompt: str
    topic: Optional[str] = None
    answer: str
    feedback: MockInterviewFeedback
    answered_at: datetime = Field(default_factory=datetime.utcnow)


class MockInterviewSectionScore(BaseModel):
    hr: float = 0.0
    technical: float = 0.0
    coding: float = 0.0


class MockInterviewSession(Document):
    user_id: str = Field(index=True)
    company_id: Optional[str] = Field(default=None, index=True)
    company_name: Optional[str] = None
    mode: MockInterviewMode = MockInterviewMode.GENERAL
    status: MockInterviewStatus = MockInterviewStatus.ACTIVE
    questions: List[MockInterviewQuestion] = Field(default_factory=list)
    answers: List[MockInterviewAnswer] = Field(default_factory=list)
    current_question_index: int = 0
    section_scores: MockInterviewSectionScore = Field(default_factory=MockInterviewSectionScore)
    overall_score: float = 0.0
    summary: str = ""
    recommendations: List[str] = Field(default_factory=list)
    comparison_summary: str = ""
    improved_areas: List[str] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "mock_interview_sessions"
        indexes = [
            "user_id",
            "company_id",
            "status",
            "started_at",
        ]
