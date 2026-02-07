from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "upskill_db"
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Judge0 API Configuration
    JUDGE0_API_URL: str
    JUDGE0_API_KEY: str
    JUDGE0_API_HOST: str
    
    # Llama Model Configuration
    LLAMA_MODEL_PATH: str = "models/llama-2-7b-chat.gguf"
    LLAMA_CONTEXT_SIZE: int = 2048
    LLAMA_MAX_TOKENS: int = 512
    
    # Application Configuration
    APP_NAME: str = "Upskill"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
