from beanie import Document, Link
from pydantic import Field, BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class PreparationCategory(str, Enum):
    APTITUDE = "aptitude"
    PROGRAMMING = "programming"
    CORE_CS = "core_cs"
    HR = "hr"

class Company(Document):
    """Company model"""
    name: str = Field(unique=True, index=True)
    description: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    interview_rounds: List[str] = Field(default_factory=list)
    important_areas: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "companies"

class InterviewFeedback(Document):
    """Model for storing uploaded interview feedback documents"""
    company_id: str = Field(index=True)
    uploader_id: str = Field(index=True)  # Admin or Senior
    file_name: str
    file_path: str
    extracted_text: Optional[str] = None
    status: str = "pending"  # pending, processed, error
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interview_feedback"

class InsightMetadata(BaseModel):
    frequently_asked_questions: List[str] = Field(default_factory=list)
    important_technical_topics: List[str] = Field(default_factory=list)
    coding_difficulty: str = "medium"  # easy, medium, hard
    common_mistakes: List[str] = Field(default_factory=list)
    preparation_tips: List[str] = Field(default_factory=list)

class RoundDetail(BaseModel):
    """Detailed information for an interview round"""
    name: str
    description: str = ""
    difficulty: str = "medium"

class CompanyInsights(Document):
    """Structured insights extracted from feedback documents"""
    company_id: str = Field(unique=True, index=True)
    rounds_summary: List[RoundDetail] = Field(default_factory=list)
    insights: InsightMetadata = Field(default_factory=InsightMetadata)
    category_mapping: Dict[str, List[str]] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "company_insights"
