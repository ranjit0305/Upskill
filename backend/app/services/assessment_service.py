from typing import List, Optional
from app.models.assessment import Question, Assessment, Submission, Answer
from app.schemas.assessment import QuestionCreate, AssessmentCreate, SubmissionCreate
from fastapi import HTTPException, status
from datetime import datetime
from app.services.performance_service import PerformanceService


class AssessmentService:
    """Assessment service for managing questions and tests"""
    
    @staticmethod
    async def create_question(question_data: QuestionCreate, created_by: str) -> Question:
        """Create a new question"""
        question = Question(
            **question_data.model_dump(),
            created_by=created_by
        )
        await question.insert()
        return question
    
    @staticmethod
    async def get_questions(
        question_type: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 50
    ) -> List[Question]:
        """Get questions with filters"""
        query = {}
        
        if question_type:
            query["type"] = question_type
        if category:
            query["category"] = category
        if difficulty:
            query["difficulty"] = difficulty
        
        questions = await Question.find(query).limit(limit).to_list()
        return questions
    
    @staticmethod
    async def create_assessment(assessment_data: AssessmentCreate, created_by: str) -> Assessment:
        """Create a new assessment"""
        # Verify all questions exist
        questions = await Question.find(
            {"_id": {"$in": assessment_data.question_ids}}
        ).to_list()
        
        if len(questions) != len(assessment_data.question_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some questions not found"
            )
        
        # Calculate total marks (1 mark per question for now)
        total_marks = len(assessment_data.question_ids)
        
        assessment = Assessment(
            title=assessment_data.title,
            description=assessment_data.description,
            type=assessment_data.type,
            questions=assessment_data.question_ids,
            duration=assessment_data.duration,
            total_marks=total_marks,
            difficulty_level=assessment_data.difficulty_level,
            created_by=created_by
        )
        
        await assessment.insert()
        return assessment
    
    @staticmethod
    async def get_assessment(assessment_id: str) -> Assessment:
        """Get assessment by ID"""
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        return assessment
    
    @staticmethod
    async def submit_assessment(
        user_id: str,
        submission_data: SubmissionCreate
    ) -> Submission:
        """Submit assessment answers and calculate score"""
        # Get assessment
        assessment = await AssessmentService.get_assessment(submission_data.assessment_id)
        
        # Get all questions
        questions = await Question.find(
            {"_id": {"$in": assessment.questions}}
        ).to_list()
        
        question_map = {str(q.id): q for q in questions}
        
        # Evaluate answers
        evaluated_answers = []
        correct_count = 0
        total_time = 0
        
        for answer_data in submission_data.answers:
            question = question_map.get(answer_data.question_id)
            if not question:
                continue
            
            is_correct = answer_data.answer.strip().lower() == question.correct_answer.strip().lower()
            if is_correct:
                correct_count += 1
            
            total_time += answer_data.time_taken
            
            evaluated_answers.append(Answer(
                question_id=answer_data.question_id,
                answer=answer_data.answer,
                is_correct=is_correct,
                time_taken=answer_data.time_taken
            ))
        
        # Calculate score and accuracy
        total_questions = len(submission_data.answers)
        accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
        score = (correct_count / assessment.total_marks * 100) if assessment.total_marks > 0 else 0
        
        # Create submission
        submission = Submission(
            user_id=user_id,
            assessment_id=submission_data.assessment_id,
            answers=evaluated_answers,
            score=score,
            accuracy=accuracy,
            time_taken=total_time
        )
        
        await submission.insert()
        
        # Trigger performance update in background (async)
        try:
            await PerformanceService.update_performance(user_id, submission)
            await PerformanceService.calculate_readiness_score(user_id)
        except Exception as e:
            # Log error but don't fail the submission
            print(f"Error updating performance: {e}")
            
        return submission
    
    @staticmethod
    async def get_assessments(limit: int = 50) -> List[Assessment]:
        """Get all available assessments"""
        assessments = await Assessment.find_all().limit(limit).to_list()
        return assessments

    @staticmethod
    async def get_user_submissions(user_id: str, limit: int = 20) -> List[Submission]:
        """Get user's submission history"""
        submissions = await Submission.find(
            Submission.user_id == user_id
        ).sort(-Submission.submitted_at).limit(limit).to_list()
        
        return submissions
    @staticmethod
    async def delete_question(question_id: str):
        """Delete a question"""
        question = await Question.get(question_id)
        if question:
            await question.delete()

    @staticmethod
    async def delete_assessment(assessment_id: str):
        """Delete an assessment"""
        assessment = await Assessment.get(assessment_id)
        if assessment:
            await assessment.delete()
