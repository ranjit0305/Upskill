from pydantic import BaseModel
from typing import List


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response"""
    total_attempts: int
    accuracy: float
    avg_speed: float
    consistency_score: float
    improvement_rate: float


class TopicPerformanceResponse(BaseModel):
    """Topic performance response"""
    topic: str
    accuracy: float
    total_questions: int
    correct_answers: int
    updated_at: str


class PerformanceResponse(BaseModel):
    """Performance response"""
    category: str
    metrics: PerformanceMetricsResponse
    topic_performance: List[TopicPerformanceResponse]
    weak_topics: List[str]
    strong_topics: List[str]
    updated_at: str


class ComponentScoreResponse(BaseModel):
    """Component score response"""
    aptitude: float
    technical: float
    coding: float
    consistency: float


class ReadinessScoreResponse(BaseModel):
    """Readiness score response"""
    overall_score: float
    component_scores: ComponentScoreResponse
    explanation: str
    recommendations: List[str]
    calculated_at: str
