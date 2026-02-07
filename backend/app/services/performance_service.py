from typing import List, Optional
from app.models.performance import Performance, ReadinessScore, PerformanceMetrics, HistoryEntry, ComponentScore
from app.models.assessment import Submission, Assessment
from datetime import datetime
import statistics


class PerformanceService:
    """Performance analytics service"""
    
    @staticmethod
    async def update_performance(user_id: str, submission: Submission):
        """Update performance metrics after a submission"""
        # Get or create performance record
        performance = await Performance.find_one(Performance.user_id == user_id)
        
        if not performance:
            performance = Performance(
                user_id=user_id,
                category="overall"
            )
        
        # Update metrics
        performance.metrics.total_attempts += 1
        
        # Add to history
        performance.history.append(HistoryEntry(
            date=submission.submitted_at,
            score=submission.score,
            accuracy=submission.accuracy
        ))
        
        # Calculate average accuracy
        if performance.history:
            accuracies = [h.accuracy for h in performance.history]
            performance.metrics.accuracy = statistics.mean(accuracies)
            
            # Calculate consistency (lower std dev = higher consistency)
            if len(accuracies) > 1:
                std_dev = statistics.stdev(accuracies)
                performance.metrics.consistency_score = max(0, 100 - std_dev)
            
            # Calculate improvement rate
            if len(performance.history) >= 2:
                recent = performance.history[-5:]  # Last 5 attempts
                if len(recent) >= 2:
                    first_avg = statistics.mean([h.accuracy for h in recent[:len(recent)//2]])
                    second_avg = statistics.mean([h.accuracy for h in recent[len(recent)//2:]])
                    performance.metrics.improvement_rate = second_avg - first_avg
        
        # Calculate average speed (questions per minute)
        if submission.time_taken > 0:
            questions_count = len(submission.answers)
            speed = questions_count / (submission.time_taken / 60)
            
            if performance.metrics.avg_speed == 0:
                performance.metrics.avg_speed = speed
            else:
                # Moving average
                performance.metrics.avg_speed = (performance.metrics.avg_speed + speed) / 2
        
        performance.updated_at = datetime.utcnow()
        await performance.save()
        
        return performance
    
    @staticmethod
    async def get_performance(user_id: str) -> Optional[Performance]:
        """Get user performance"""
        return await Performance.find_one(Performance.user_id == user_id)
    
    @staticmethod
    async def calculate_readiness_score(user_id: str) -> ReadinessScore:
        """Calculate placement readiness score"""
        # Get all user submissions
        submissions = await Submission.find(Submission.user_id == user_id).to_list()
        
        if not submissions:
            # Return default score for new users
            return ReadinessScore(
                user_id=user_id,
                overall_score=0,
                explanation="No assessment data available yet. Start taking tests to get your readiness score!",
                recommendations=[
                    "Take aptitude tests to assess your quantitative and logical skills",
                    "Complete technical MCQs to evaluate your core CS knowledge",
                    "Solve coding problems to improve problem-solving abilities"
                ]
            )
        
        # Get all related assessments to know their types
        assessment_ids = list(set([s.assessment_id for s in submissions]))
        assessments = await Assessment.find({"_id": {"$in": assessment_ids}}).to_list()
        assessment_type_map = {str(a.id): a.type for a in assessments}
        
        # Calculate component scores
        aptitude_submissions = [s for s in submissions if assessment_type_map.get(s.assessment_id) == "aptitude"]
        technical_submissions = [s for s in submissions if assessment_type_map.get(s.assessment_id) == "technical"]
        coding_submissions = [s for s in submissions if assessment_type_map.get(s.assessment_id) == "coding"]
        
        component_scores = ComponentScore()
        
        if aptitude_submissions:
            component_scores.aptitude = statistics.mean([s.accuracy for s in aptitude_submissions])
        
        if technical_submissions:
            component_scores.technical = statistics.mean([s.accuracy for s in technical_submissions])
        
        if coding_submissions:
            component_scores.coding = statistics.mean([s.accuracy for s in coding_submissions])
        
        # Calculate consistency
        if len(submissions) > 1:
            accuracies = [s.accuracy for s in submissions]
            std_dev = statistics.stdev(accuracies)
            component_scores.consistency = max(0, 100 - std_dev)
        
        # Calculate overall score (weighted average)
        weights = {
            "aptitude": 0.25,
            "technical": 0.30,
            "coding": 0.35,
            "consistency": 0.10
        }
        
        overall_score = (
            component_scores.aptitude * weights["aptitude"] +
            component_scores.technical * weights["technical"] +
            component_scores.coding * weights["coding"] +
            component_scores.consistency * weights["consistency"]
        )
        
        # Generate explanation and recommendations
        explanation = PerformanceService._generate_explanation(overall_score, component_scores)
        recommendations = PerformanceService._generate_recommendations(component_scores)
        
        # Get or create readiness score
        readiness = await ReadinessScore.find_one(ReadinessScore.user_id == user_id)
        
        if not readiness:
            readiness = ReadinessScore(user_id=user_id)
        
        readiness.overall_score = overall_score
        readiness.component_scores = component_scores
        readiness.explanation = explanation
        readiness.recommendations = recommendations
        readiness.calculated_at = datetime.utcnow()
        
        await readiness.save()
        return readiness
    
    @staticmethod
    def _generate_explanation(overall_score: float, components: ComponentScore) -> str:
        """Generate explanation for readiness score"""
        if overall_score >= 80:
            level = "Excellent! You're well-prepared for placements."
        elif overall_score >= 60:
            level = "Good progress! You're on the right track."
        elif overall_score >= 40:
            level = "Moderate preparation. Focus on weak areas."
        else:
            level = "Needs improvement. Consistent practice required."
        
        return f"{level} Your aptitude score is {components.aptitude:.1f}%, technical knowledge is at {components.technical:.1f}%, and coding skills are at {components.coding:.1f}%."
    
    @staticmethod
    def _generate_recommendations(components: ComponentScore) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if components.aptitude < 60:
            recommendations.append("Focus on aptitude practice - solve more quantitative and logical reasoning problems")
        
        if components.technical < 60:
            recommendations.append("Strengthen technical fundamentals - review OS, DBMS, Networks, and OOP concepts")
        
        if components.coding < 60:
            recommendations.append("Improve coding skills - practice data structures and algorithms daily")
        
        if components.consistency < 50:
            recommendations.append("Maintain consistency - practice regularly to build momentum")
        
        if not recommendations:
            recommendations.append("Excellent work! Continue practicing to maintain your performance")
            recommendations.append("Start focusing on company-specific preparation")
        
        return recommendations
