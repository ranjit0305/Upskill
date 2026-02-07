from beanie import Document
from pydantic import EmailStr, Field, BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    STUDENT = "student"
    SENIOR = "senior"
    ADMIN = "admin"


class UserProfile(BaseModel):
    """User profile information"""
    name: str
    college: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None
    target_companies: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class User(Document):
    """User model for all user types"""
    
    email: EmailStr = Field(unique=True, index=True)
    password_hash: str
    role: UserRole
    profile: UserProfile
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "role",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "role": "student",
                "profile": {
                    "name": "John Doe",
                    "college": "ABC University",
                    "branch": "Computer Science",
                    "year": 3,
                    "target_companies": ["Google", "Microsoft"],
                    "skills": ["Python", "JavaScript", "React"]
                }
            }
        }



