from typing import List, Optional, Union
from app.models.assessment import Question, Assessment, Submission, Answer, QuestionType, DifficultyLevel
from app.schemas.assessment import QuestionCreate, AssessmentCreate, SubmissionCreate
from fastapi import HTTPException, status
from datetime import datetime
from app.services.performance_service import PerformanceService


class AssessmentService:
    """Assessment service for managing questions and tests"""
    COMPANY_APTITUDE_TARGET = 20
    COMPANY_TECHNICAL_TARGET = 20
    COMPANY_CODING_TARGET = 4
    
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
        from app.services.coding_service import CodingService
        
        # Get assessment
        assessment = await AssessmentService.get_assessment(submission_data.assessment_id)
        
        # Get all questions using ObjectIds for correctness
        from bson import ObjectId
        question_ids = [ObjectId(qid) for qid in assessment.questions if ObjectId.is_valid(qid)]
        questions = await Question.find({"_id": {"$in": question_ids}}).to_list()
        
        question_map = {str(q.id): q for q in questions}
        
        # Evaluate answers
        evaluated_answers = []
        mcq_correct_count = 0
        mcq_total_count = 0
        coding_points = 0.0
        coding_total_count = 0
        total_time = submission_data.time_taken or 0
        if total_time == 0:
            total_time = sum(a.time_taken for a in submission_data.answers)
        
        for answer_data in submission_data.answers:
            question = question_map.get(answer_data.question_id)
            if not question:
                continue
            
            # total_time already calculated
            
            if question.type == QuestionType.CODING:
                coding_total_count += 1
                evaluated_answer = await CodingService.evaluate_coding_answer(
                    question=question,
                    code=answer_data.code,
                    language=answer_data.language,
                    time_taken=answer_data.time_taken
                )
                coding_points += CodingService.calculate_coding_points(evaluated_answer)
                evaluated_answers.append(evaluated_answer)
            else:
                mcq_total_count += 1
                is_correct = False
                if answer_data.answer:
                    is_correct = answer_data.answer.strip().lower() == question.correct_answer.strip().lower()
                
                if is_correct:
                    mcq_correct_count += 1
                
                evaluated_answers.append(Answer(
                    question_id=answer_data.question_id,
                    answer=answer_data.answer,
                    is_correct=is_correct,
                    time_taken=answer_data.time_taken
                ))
        
        # Calculate scores
        # MCQ Score (percentage of MCQ questions correct)
        mcq_score = (mcq_correct_count / mcq_total_count * 100) if mcq_total_count > 0 else 0
        
        # Coding Score (percentage of coding test cases passed)
        coding_score = (coding_points / coding_total_count * 100) if coding_total_count > 0 else 0
        
        # Total Score (weighted average or simple average)
        # For now, let's treat each question as equal weight (1 mark each)
        total_marks = mcq_total_count + coding_total_count
        raw_score = mcq_correct_count + coding_points
        total_score_pct = (raw_score / total_marks * 100) if total_marks > 0 else 0
        
        # Accuracy
        accuracy = total_score_pct # Similar to total score for now
        
        # Create submission
        submission = Submission(
            user_id=user_id,
            assessment_id=submission_data.assessment_id,
            answers=evaluated_answers,
            score=mcq_score,
            coding_score=coding_score,
            total_score=total_score_pct,
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
    async def evaluate_single_question(
        assessment_id: str,
        question_id: str,
        code: str,
        language: str
    ) -> dict:
        """Evaluate a single coding question against all test cases without saving a full submission"""
        from app.services.coding_service import CodingService
        
        # Verify assessment and question relationship
        assessment = await Assessment.get(assessment_id)
        if not assessment or question_id not in assessment.questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found in this assessment"
            )
            
        question = await Question.get(question_id)
        if not question or question.type != QuestionType.CODING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not a coding question"
            )
            
        # Evaluate using CodingService (runs all test cases)
        evaluated_answer = await CodingService.evaluate_coding_answer(
            question=question,
            code=code,
            language=language,
            time_taken=0
        )
        
        # Calculate points
        points = CodingService.calculate_coding_points(evaluated_answer)
        
        return {
            "question_id": question_id,
            "passed": evaluated_answer.is_correct,
            "score": points * 100, # Percentage score for this question
            "test_results": evaluated_answer.test_results,
            "total_test_cases": len(question.test_cases) if question.test_cases else 0,
            "passed_test_cases": sum(1 for tr in evaluated_answer.test_results if tr.get("passed"))
        }

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
    async def create_company_aptitude_test(company_id: str, user_id: str) -> Assessment:
        """
        Dynamically generate or fetch an aptitude test using only company-specific generated questions.
        """
        from app.models.company import Company
        company = await Company.get(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        final_qs = await Question.find({
            "companies": {"$in": [company_id]},
            "tags": {"$in": ["source:feedback", "source:web"]},
            "type": QuestionType.APTITUDE
        }).sort(-Question.created_at).to_list()

        if not final_qs:
            raise HTTPException(
                status_code=404,
                detail="No company-specific aptitude questions available yet. Upload feedback or sync interview experiences first."
            )

        # 4. Create/Get the Assessment
        existing_test = await Assessment.find_one({
            "type": QuestionType.APTITUDE,
            "is_generated": True,
            "description": {"$regex": company_id} 
        })
        
        selected_questions = final_qs[: min(len(final_qs), AssessmentService.COMPANY_APTITUDE_TARGET)]
        if existing_test:
            existing_test.questions = [str(q.id) for q in selected_questions]
            existing_test.total_marks = len(selected_questions)
            existing_test.duration = max(15, len(selected_questions) * 3)
            await existing_test.save()
            return existing_test
            
        assessment = Assessment(
            title=f"Aptitude Practice Test",
            description=f"A company-specific aptitude test for {company_id} generated from uploaded feedback and synced interview experiences.",
            type=QuestionType.APTITUDE,
            questions=[str(q.id) for q in selected_questions],
            duration=max(15, len(selected_questions) * 3),
            total_marks=len(selected_questions),
            difficulty_level=DifficultyLevel.MEDIUM,
            is_generated=True,
            created_by=user_id
        )
        await assessment.insert()
        return assessment

    @staticmethod
    async def get_assessment_questions(assessment_id: str) -> List[Question]:
        """Fetch questions for a test without correct answers"""
        from beanie import PydanticObjectId
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            return []
        
        # Convert string IDs back to PydanticObjectId for the $in query
        q_ids = []
        for q_id in assessment.questions:
            try:
                q_ids.append(PydanticObjectId(q_id))
            except:
                pass

        questions = await Question.find({
            "_id": {"$in": q_ids}
        }).to_list()
        
        # Sort based on the order in the assessment
        q_map = {str(q.id): q for q in questions}
        return [q_map[qid] for qid in assessment.questions if qid in q_map]

    @staticmethod
    async def create_company_coding_test(company_id: str, user_id: str) -> Assessment:
        """
        Dynamically generate or fetch a coding test using only company-specific generated questions.
        """
        from app.models.company import Company
        company = await Company.get(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        final_qs = await Question.find({
            "companies": {"$in": [company_id]},
            "tags": {"$in": ["source:feedback", "source:web"]},
            "type": QuestionType.CODING
        }).sort(-Question.created_at).to_list()

        if not final_qs:
            raise HTTPException(
                status_code=404,
                detail="No company-specific coding questions available yet. Upload feedback or sync interview experiences first."
            )

        # 3. Create/Get the Assessment
        existing_test = await Assessment.find_one({
            "type": QuestionType.CODING,
            "is_generated": True,
            "description": {"$regex": company_id} 
        })
        
        selected_questions = final_qs[: min(len(final_qs), AssessmentService.COMPANY_CODING_TARGET)]
        q_ids = [str(q.id) for q in selected_questions]

        if existing_test:
            existing_test.questions = q_ids
            existing_test.total_marks = len(q_ids)
            existing_test.duration = max(30, len(q_ids) * 20)
            await existing_test.save()
            return existing_test
            
        assessment = Assessment(
            title=f"Coding Assessment",
            description=f"A company-specific coding test for {company_id} generated from uploaded feedback and synced interview experiences.",
            type=QuestionType.CODING,
            questions=q_ids,
            duration=max(30, len(q_ids) * 20),
            total_marks=len(q_ids),
            difficulty_level=DifficultyLevel.MEDIUM,
            is_generated=True,
            created_by=user_id
        )
        await assessment.insert()
        return assessment

    @staticmethod
    async def create_company_technical_test(company_id: str, user_id: str) -> Assessment:
        """
        Dynamically generate or fetch a technical test using only company-specific generated questions.
        """
        from app.models.company import Company
        company = await Company.get(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        final_qs = await Question.find({
            "companies": {"$in": [company_id]},
            "tags": {"$in": ["source:feedback", "source:web"]},
            "type": QuestionType.TECHNICAL
        }).sort(-Question.created_at).to_list()

        if not final_qs:
            raise HTTPException(
                status_code=404,
                detail="No company-specific technical questions available yet. Upload feedback or sync interview experiences first."
            )

        # 3. Create/Get the Assessment
        existing_test = await Assessment.find_one({
            "type": QuestionType.TECHNICAL,
            "is_generated": True,
            "description": {"$regex": company_id} 
        })
        
        selected_questions = final_qs[: min(len(final_qs), AssessmentService.COMPANY_TECHNICAL_TARGET)]
        q_ids = [str(q.id) for q in selected_questions]

        if existing_test:
            existing_test.questions = q_ids
            existing_test.total_marks = len(q_ids)
            existing_test.duration = max(15, len(q_ids) * 2)
            await existing_test.save()
            return existing_test
            
        assessment = Assessment(
            title=f"Technical Assessment",
            description=f"A company-specific technical test for {company_id} generated from uploaded feedback and synced interview experiences.",
            type=QuestionType.TECHNICAL,
            questions=q_ids,
            duration=max(15, len(q_ids) * 2),
            total_marks=len(q_ids),
            difficulty_level=DifficultyLevel.MEDIUM,
            is_generated=True,
            created_by=user_id
        )
        await assessment.insert()
        return assessment
