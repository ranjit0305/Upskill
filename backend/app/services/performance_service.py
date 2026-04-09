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
        from app.models.assessment import Question
        
        # Get or create performance record
        performance = await Performance.find_one(Performance.user_id == user_id)
        
        if not performance:
            performance = Performance(
                user_id=user_id,
                category="overall"
            )
        
        # Update overall metrics
        performance.metrics.total_attempts += 1
        
        # Add to history
        performance.history.append(HistoryEntry(
            date=submission.submitted_at,
            score=submission.score,
            accuracy=submission.accuracy
        ))
        
        # Topic-wise performance update
        question_ids = [a.question_id for a in submission.answers]
        
        from bson import ObjectId
        obj_ids = [ObjectId(qid) for qid in question_ids if ObjectId.is_valid(qid)]
        questions = await Question.find({"_id": {"$in": obj_ids}}).to_list()
        
        question_map = {str(q.id): q for q in questions}
        
        topic_counts = {} # topic -> {total, correct}
        
        for answer in submission.answers:
            q = question_map.get(answer.question_id)
            if not q:
                continue
                
            topic = q.category
            if topic not in topic_counts:
                topic_counts[topic] = {"total": 0, "correct": 0}
            
            topic_counts[topic]["total"] += 1
            if answer.is_correct:
                topic_counts[topic]["correct"] += 1
        
        # Update performance.topic_performance
        for topic, counts in topic_counts.items():
            # Find existing topic performance or create new
            tp = next((x for x in performance.topic_performance if x.topic == topic), None)
            if not tp:
                from app.models.performance import TopicPerformance
                tp = TopicPerformance(topic=topic)
                performance.topic_performance.append(tp)
            
            tp.total_questions += counts["total"]
            tp.correct_answers += counts["correct"]
            tp.accuracy = (tp.correct_answers / tp.total_questions * 100)
            tp.updated_at = datetime.utcnow()
        
        # Update weak and strong topics
        performance.weak_topics = [
            tp.topic for tp in performance.topic_performance 
            if tp.accuracy < 50 and tp.total_questions >= 3
        ]
        performance.strong_topics = [
            tp.topic for tp in performance.topic_performance 
            if tp.accuracy >= 80 and tp.total_questions >= 3
        ]

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
        performance = await PerformanceService.get_performance(user_id)
        explanation = PerformanceService._generate_explanation(overall_score, component_scores)
        recommendations = PerformanceService._generate_recommendations(component_scores, performance)
        
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
    def _generate_recommendations(components: ComponentScore, performance: Optional[Performance] = None) -> List[str]:
        """Generate personalized recommendations based on component scores and specific weak topics"""
        recommendations = []
        
        # Topic-specific recommendations
        if performance and performance.weak_topics:
            topics_str = ", ".join(performance.weak_topics[:3])
            recommendations.append(f"Immediate Focus: You're struggling with {topics_str}. Practice more questions from these specific areas.")

        if components.aptitude < 60:
            recommendations.append("Aptitude Boost: Focus on Quantitative and Logical reasoning basics.")
        
        if components.technical < 60:
            recommendations.append("Technical Review: Revisit core CS fundamentals like OS, DBMS, and Networking.")
        
        if components.coding < 60:
            recommendations.append("Coding Practice: Solve at least 2 problems daily to improve your logic building.")
        
        if components.consistency < 50:
            recommendations.append("Daily Habit: Try to take at least one small quiz every day to improve consistency.")
        
        if not recommendations:
            recommendations.append("Excellent work! Continue practicing to maintain your performance.")
            recommendations.append("Level Up: Start solving 'Hard' difficulty problems for your top companies.")
        
        return recommendations
