from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.mock_interview import (
    MockInterviewMode,
    MockInterviewStatus,
    MockQuestionCategory,
)


class MockInterviewStartRequest(BaseModel):
    mode: MockInterviewMode = MockInterviewMode.GENERAL
    company_id: Optional[str] = None
    question_count: int = Field(default=6, ge=3, le=9)


class MockInterviewQuestionResponse(BaseModel):
    index: int
    category: MockQuestionCategory
    prompt: str
    topic: Optional[str] = None
    difficulty: str
    source: str


class MockInterviewSectionScoreResponse(BaseModel):
    hr: float = 0.0
    technical: float = 0.0
    coding: float = 0.0


class MockInterviewFeedbackResponse(BaseModel):
    relevance: float
    clarity: float
    structure: float
    technical_accuracy: float
    confidence: float
    score: float
    strengths: List[str]
    improvements: List[str]
    suggested_answer: str


class MockInterviewAnswerItemResponse(BaseModel):
    question_index: int
    category: MockQuestionCategory
    prompt: str
    topic: Optional[str] = None
    answer: str
    feedback: MockInterviewFeedbackResponse
    answered_at: str


class MockInterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=10, max_length=4000)


class MockInterviewSessionResponse(BaseModel):
    id: str
    mode: MockInterviewMode
    status: MockInterviewStatus
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    current_question_index: int
    total_questions: int
    current_question: Optional[MockInterviewQuestionResponse] = None
    section_scores: MockInterviewSectionScoreResponse
    overall_score: float
    summary: str
    recommendations: List[str]
    comparison_summary: str = ""
    improved_areas: List[str] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)
    answers: List[MockInterviewAnswerItemResponse] = Field(default_factory=list)
    started_at: str
    completed_at: Optional[str] = None


class MockInterviewAnswerResponse(BaseModel):
    session: MockInterviewSessionResponse
    feedback: MockInterviewFeedbackResponse
    next_question: Optional[MockInterviewQuestionResponse] = None
    completed: bool


class MockInterviewHistoryItem(BaseModel):
    id: str
    mode: MockInterviewMode
    status: MockInterviewStatus
    company_name: Optional[str] = None
    overall_score: float
    started_at: str
    completed_at: Optional[str] = None
    total_questions: int
    answered_questions: int


class MockInterviewHistoryResponse(BaseModel):
    sessions: List[MockInterviewHistoryItem]
