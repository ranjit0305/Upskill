from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.models.performance import Performance, ReadinessScore
from app.models.assessment import Submission
from typing import List, Dict, Any
from datetime import datetime

class CompanyService:
    @staticmethod
    async def get_company_prep_dashboard(user_id: str, company_id: str) -> Dict[str, Any]:
        """Combine company insights and user performance for the dashboard"""
        from beanie import PydanticObjectId
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Handle both string and ObjectId lookups
            lookup_id = None
            if isinstance(company_id, str) and len(company_id) == 24:
                try:
                    lookup_id = PydanticObjectId(company_id)
                except:
                    pass
            
            if lookup_id:
                company = await Company.get(lookup_id)
            else:
                company = await Company.find_one(Company.id == company_id)
                
            if not company:
                logger.warning(f"Company not found in DB: {company_id}")
                return None
                
            insights = await CompanyInsights.find_one(CompanyInsights.company_id == str(company.id))
            
            # Calculate company-specific readiness
            readiness = await CompanyService.calculate_readiness(user_id, str(company.id))
            
            # Generate personalized recommendations
            learning_path = await CompanyService.generate_learning_path(user_id, str(company.id), insights)
            
            # Fetch questions generated based on this company's feedback
            from app.models.assessment import Question
            generated_questions = await Question.find({"companies": str(company.id)}).limit(10).to_list()
            
            return {
                "company": company,
                "insights": insights,
                "readiness_score": readiness,
                "learning_path": learning_path,
                "generated_questions": generated_questions
            }
        except Exception as e:
            logger.error(f"Error in get_company_prep_dashboard for {company_id}: {str(e)}", exc_info=True)
            # Re-raise so it becomes a 500 error instead of a mysterious 404
            raise

    @staticmethod
    async def calculate_readiness(user_id: str, company_id: str) -> float:
        """
        Calculate a Zoho-specific readiness score (0–100).
        Logic: Weight user's performance in categories important to the company.
        """
        # Fetch overall performance
        performances = await Performance.find(Performance.user_id == user_id).to_list()
        perf_map = {p.category: p.metrics.accuracy for p in performances}
        
        # Default weights for Zoho (could be dynamic based on insights in future)
        weights = {
            "aptitude": 0.3,
            "technical": 0.3,
            "coding": 0.4
        }
        
        score = 0.0
        total_weight = 0.0
        
        for category, weight in weights.items():
            if category in perf_map:
                score += perf_map[category] * weight
            total_weight += weight
            
        final_score = (score / total_weight) * 100 if total_weight > 0 else 0
        return round(final_score, 2)

    @staticmethod
    async def generate_learning_path(user_id: str, company_id: str, insights: CompanyInsights) -> List[Dict[str, Any]]:
        """Prioritize topics based on frequency in feedback and user weakness"""
        if not insights:
            return []
            
        performance = await Performance.find_one(Performance.user_id == user_id, Performance.category == "overall")
        weak_topics = performance.weak_topics if performance else []
        
        learning_path = []
        
        # High priority: Topics important to Zoho and weak for user
        company_topics = insights.insights.important_technical_topics
        
        for topic in company_topics:
            priority = "high" if topic in weak_topics else "medium"
            learning_path.append({
                "topic": topic,
                "priority": priority,
                "reason": "Frequently asked in Zoho interviews" if priority == "medium" else "Critical topic and needs improvement"
            })
            
        return learning_path
