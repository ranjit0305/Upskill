from fastapi import APIRouter, Depends, HTTPException, status
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.models.user import UserRole
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer()

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to verify admin privileges"""
    user = await AuthService.get_current_user(credentials.credentials)
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

@router.get("/stats", response_model=Dict[str, Any])
async def get_platform_stats(admin = Depends(get_admin_user)):
    """Get high-level platform analytics"""
    return await AdminService.get_system_stats()

@router.get("/distribution", response_model=List[Dict[str, Any]])
async def get_question_dist(admin = Depends(get_admin_user)):
    """Get distribution of questions by category"""
    return await AdminService.get_question_distribution()
