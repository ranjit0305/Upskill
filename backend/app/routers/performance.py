from fastapi import APIRouter, Depends
from app.schemas.performance import PerformanceResponse, ReadinessScoreResponse, PerformanceMetricsResponse, ComponentScoreResponse
from app.services.performance_service import PerformanceService
from app.services.auth_service import AuthService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/performance", tags=["Performance"])
security = HTTPBearer()


async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user"""
    return await AuthService.get_current_user(credentials.credentials)


@router.get("/me", response_model=PerformanceResponse)
async def get_my_performance(current_user = Depends(get_current_user_from_token)):
    """Get current user's performance metrics"""
    performance = await PerformanceService.get_performance(str(current_user.id))
    
    if not performance:
        # Return default performance for new users
        from app.models.performance import PerformanceMetrics
        return PerformanceResponse(
            category="overall",
            metrics=PerformanceMetricsResponse(
                total_attempts=0,
                accuracy=0.0,
                avg_speed=0.0,
                consistency_score=0.0,
                improvement_rate=0.0
            ),
            weak_topics=[],
            strong_topics=[],
            updated_at=""
        )
    
    return PerformanceResponse(
        category=performance.category,
        metrics=PerformanceMetricsResponse(
            total_attempts=performance.metrics.total_attempts,
            accuracy=performance.metrics.accuracy,
            avg_speed=performance.metrics.avg_speed,
            consistency_score=performance.metrics.consistency_score,
            improvement_rate=performance.metrics.improvement_rate
        ),
        weak_topics=performance.weak_topics,
        strong_topics=performance.strong_topics,
        updated_at=performance.updated_at.isoformat()
    )


@router.get("/readiness", response_model=ReadinessScoreResponse)
async def get_readiness_score(current_user = Depends(get_current_user_from_token)):
    """Get placement readiness score"""
    readiness = await PerformanceService.calculate_readiness_score(str(current_user.id))
    
    return ReadinessScoreResponse(
        overall_score=readiness.overall_score,
        component_scores=ComponentScoreResponse(
            aptitude=readiness.component_scores.aptitude,
            technical=readiness.component_scores.technical,
            coding=readiness.component_scores.coding,
            consistency=readiness.component_scores.consistency
        ),
        explanation=readiness.explanation,
        recommendations=readiness.recommendations,
        calculated_at=readiness.calculated_at.isoformat()
    )
