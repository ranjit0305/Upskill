from typing import Dict, Any, List
from app.models.user import User, UserRole
from app.models.assessment import Question, Assessment, Submission
from app.models.performance import ReadinessScore
import statistics

class AdminService:
    """Admin-only services for analytics and management"""
    
    @staticmethod
    async def get_system_stats() -> Dict[str, Any]:
        """Get high-level system analytics"""
        user_count = await User.count()
        student_count = await User.find(User.role == UserRole.STUDENT).count()
        senior_count = await User.find(User.role == UserRole.SENIOR).count()
        
        question_count = await Question.count()
        assessment_count = await Assessment.count()
        submission_count = await Submission.count()
        
        # Calculate average readiness score across all students
        readiness_scores = await ReadinessScore.find_all().to_list()
        avg_readiness = 0
        if readiness_scores:
            avg_readiness = statistics.mean([r.overall_score for r in readiness_scores])
            
        return {
            "users": {
                "total": user_count,
                "students": student_count,
                "seniors": senior_count
            },
            "content": {
                "questions": question_count,
                "assessments": assessment_count,
                "submissions": submission_count
            },
            "performance": {
                "avg_readiness": round(avg_readiness, 2)
            }
        }

    @staticmethod
    async def get_question_distribution() -> List[Dict[str, Any]]:
        """Get distribution of questions by category"""
        # This is a simplified version; in production, use MongoDB aggregation
        questions = await Question.find_all().to_list()
        distribution = {}
        for q in questions:
            cat = q.category
            distribution[cat] = distribution.get(cat, 0) + 1
            
        return [{"category": k, "count": v} for k, v in distribution.items()]
