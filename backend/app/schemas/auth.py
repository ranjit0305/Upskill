from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole, UserProfile


class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole
    profile: UserProfile
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "SecurePass123!",
                "role": "student",
                "profile": {
                    "name": "John Doe",
                    "college": "ABC University",
                    "branch": "Computer Science",
                    "year": 3
                }
            }
        }


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "SecurePass123!"
            }
        }


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: EmailStr
    role: UserRole
    profile: UserProfile
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True
