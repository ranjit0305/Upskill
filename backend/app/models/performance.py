from beanie import Document
from pydantic import Field, BaseModel
from typing import List, Optional
from datetime import datetime


class PerformanceMetrics(BaseModel):
    """Performance metrics model"""
    total_attempts: int = 0
    accuracy: float = 0.0
    avg_speed: float = 0.0  # questions per minute
    consistency_score: float = 0.0
    improvement_rate: float = 0.0


class HistoryEntry(BaseModel):
    """Performance history entry"""
    date: datetime
    score: float
    accuracy: float


class Performance(Document):
    """Performance tracking model"""
    
    user_id: str = Field(unique=True, index=True)
    category: str  # "overall", "aptitude", "technical", "coding"
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    history: List[HistoryEntry] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "performance"
        indexes = [
            "user_id",
            "category",
        ]


class ComponentScore(BaseModel):
    """Component score breakdown"""
    aptitude: float = 0.0
    technical: float = 0.0
    coding: float = 0.0
    consistency: float = 0.0


class CompanyScore(BaseModel):
    """Company-specific readiness score"""
    company: str
    score: float
    gaps: List[str] = Field(default_factory=list)


class ReadinessScore(Document):
    """Readiness score model"""
    
    user_id: str = Field(unique=True, index=True)
    overall_score: float = 0.0  # 0-100
    component_scores: ComponentScore = Field(default_factory=ComponentScore)
    explanation: str = ""
    recommendations: List[str] = Field(default_factory=list)
    company_specific: List[CompanyScore] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "readiness_scores"
        indexes = [
            "user_id",
        ]
