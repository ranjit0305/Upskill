from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager"""
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB database"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
            
            # Import all models here
            from app.models.user import User
            from app.models.assessment import Question, Assessment, Submission
            from app.models.performance import Performance, ReadinessScore
            from app.models.company import Company, InterviewFeedback, CompanyInsights
            
            # Initialize Beanie with models
            await init_beanie(
                database=cls.client[settings.DATABASE_NAME],
                document_models=[
                    User,
                    Question,
                    Assessment,
                    Submission,
                    Performance,
                    ReadinessScore,
                    Company,
                    InterviewFeedback,
                    CompanyInsights
                ]
            )
            
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")


# Database instance
db = Database()
