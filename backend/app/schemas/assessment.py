from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.assessment import QuestionType, DifficultyLevel


class QuestionCreate(BaseModel):
    """Schema for creating a question"""
    type: QuestionType
    category: str
    difficulty: DifficultyLevel
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    tags: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    test_cases: Optional[List[dict]] = None


class QuestionResponse(BaseModel):
    """Schema for question response (without correct answer)"""
    id: str
    type: QuestionType
    category: str
    difficulty: DifficultyLevel
    question: str
    options: Optional[List[str]] = None
    sample_input: Optional[str] = None
    sample_output: Optional[str] = None
    test_cases_count: int = 0
    tags: List[str]
    companies: List[str]
    
    class Config:
        from_attributes = True


class QuestionDetail(QuestionResponse):
    """Schema for question with answer (for admins)"""
    correct_answer: str
    explanation: str
    test_cases: Optional[List[dict]] = None


class AssessmentCreate(BaseModel):
    """Schema for creating an assessment"""
    title: str
    description: Optional[str] = None
    type: QuestionType
    question_ids: List[str]
    duration: int
    difficulty_level: DifficultyLevel


class AssessmentResponse(BaseModel):
    """Schema for assessment response"""
    id: str
    title: str
    description: Optional[str]
    type: QuestionType
    duration: int
    total_marks: int
    difficulty_level: DifficultyLevel
    question_count: int
    
    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    """Schema for submitting an answer"""
    question_id: str
    answer: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    time_taken: int = 0


class SubmissionCreate(BaseModel):
    """Schema for creating a submission"""
    assessment_id: str
    answers: List[AnswerSubmit]
    time_taken: Optional[int] = 0


class SubmissionResponse(BaseModel):
    """Schema for submission response"""
    id: str
    assessment_id: str
    score: float
    coding_score: float = 0.0
    total_score: float = 0.0
    accuracy: float
    time_taken: int
    submitted_at: str
    
    class Config:
        from_attributes = True


class SubmissionDetail(SubmissionResponse):
    """Schema for detailed submission with answers"""
    answers: List[dict]
