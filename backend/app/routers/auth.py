from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    user = await AuthService.register_user(user_data)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        profile=user.profile,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user and return tokens"""
    user = await AuthService.authenticate_user(login_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    tokens = await AuthService.create_tokens(user)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    user = await AuthService.get_current_user(token)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        profile=user.profile,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token using refresh token"""
    token = credentials.credentials
    user = await AuthService.get_current_user(token)
    
    tokens = await AuthService.create_tokens(user)
    return tokens
