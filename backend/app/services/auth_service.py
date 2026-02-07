from typing import Optional
from datetime import datetime
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from fastapi import HTTPException, status


class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def register_user(user_data: UserRegister) -> User:
        """Register a new user"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if user already exists
        try:
            existing_user = await User.find_one(User.email == user_data.email)
            if existing_user:
                logger.warning(f"Registration failed: Email {user_data.email} already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create new user
            user = User(
                email=user_data.email,
                password_hash=get_password_hash(user_data.password),
                role=user_data.role,
                profile=user_data.profile
            )
            
            await user.insert()
            logger.info(f"Successfully registered user: {user_data.email}")
            return user
        except Exception as e:
            if not isinstance(e, HTTPException):
                logger.error(f"Unexpected error during registration for {user_data.email}: {e}")
            raise
    
    @staticmethod
    async def authenticate_user(login_data: UserLogin) -> Optional[User]:
        """Authenticate user credentials"""
        import logging
        logger = logging.getLogger(__name__)
        
        user = await User.find_one(User.email == login_data.email)
        
        if not user:
            logger.warning(f"Login failed: User {login_data.email} not found")
            return None
        
        try:
            is_verified = verify_password(login_data.password, user.password_hash)
            if not is_verified:
                logger.warning(f"Login failed: Password mismatch for {login_data.email}")
                return None
        except Exception as e:
            logger.error(f"Error during verify_password for {login_data.email}: {e}")
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.save()
        
        return user
    
    @staticmethod
    async def create_tokens(user: User) -> Token:
        """Create access and refresh tokens"""
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    @staticmethod
    async def get_current_user(token: str) -> User:
        """Get current user from token"""
        payload = decode_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await User.find_one(User.email == email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
