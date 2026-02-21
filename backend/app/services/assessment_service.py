from typing import List, Optional, Union
from app.models.assessment import Question, Assessment, Submission, Answer, QuestionType, DifficultyLevel
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
        from app.services.coding_service import CodingService
        
        # Get assessment
        assessment = await AssessmentService.get_assessment(submission_data.assessment_id)
        
        # Get all questions
        questions = await Question.find(
            {"_id": {"$in": assessment.questions}}
        ).to_list()
        
        question_map = {str(q.id): q for q in questions}
        
        # Evaluate answers
        evaluated_answers = []
        mcq_correct_count = 0
        mcq_total_count = 0
        coding_points = 0.0
        coding_total_count = 0
        total_time = 0
        
        for answer_data in submission_data.answers:
            question = question_map.get(answer_data.question_id)
            if not question:
                continue
            
            total_time += answer_data.time_taken
            
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
        Dynamically generate or fetch a 50-question Aptitude test for a company.
        """
        from app.models.company import Company, CompanyInsights
        from beanie import PydanticObjectId
        import random

        # 0. Get company info
        company = await Company.get(company_id)
        company_name = company.name.lower() if company else company_id.lower()

        # 1. Get company topics
        insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
        apt_topics = []
        if insights and insights.insights.important_technical_topics:
            # Detect aptitude-specific topics from technical topics or overall text
            # NOTE: We only import AIService if topics are found or we reach critical threshold
            from app.services.ai_service import AIService
            all_text = " ".join(insights.insights.important_technical_topics)
            apt_topics = AIService._extract_aptitude_topics(all_text)
        
        if not apt_topics:
            apt_topics = ["profit_and_loss", "time_and_work", "speed_distance_time", "logical_reasoning", "percentages"]

        # 2. Collect Questions
        # Priority 1: Questions already tagged with this company ID or Name
        search_terms = list(set([company_id, company_name]))
        if "zoho" in company_name:
            search_terms.append("zoho")
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generating aptitude test for {company_name} (ID: {company_id}) using search terms: {search_terms}")

        existing_company_qs = await Question.find({
            "companies": {"$in": search_terms},
            "type": QuestionType.APTITUDE
        }).to_list()
        
        final_qs = existing_company_qs
        
        # Priority 2: Questions matching the detected topics
        if len(final_qs) < 50:
            topic_qs = await Question.find({
                "category": {"$in": apt_topics},
                "type": QuestionType.APTITUDE,
                "_id": {"$nin": [q.id for q in final_qs]}
            }).limit(50 - len(final_qs)).to_list()
            final_qs.extend(topic_qs)
        
        # Priority 3: Fallback random aptitude questions
        if len(final_qs) < 50:
            fallback_qs = await Question.find({
                "type": QuestionType.APTITUDE,
                "_id": {"$nin": [q.id for q in final_qs]}
            }).limit(50 - len(final_qs)).to_list()
            final_qs.extend(fallback_qs)

        # 3. If STILL missing or under 50, fill from internal bank using AIService
        if len(final_qs) < 50:
            # We use a threshold for AI mass generation, but we always fill from bank
            for topic in apt_topics:
                if len(final_qs) >= 50: break
                from app.services.ai_service import AIService
                bank = AIService.APTITUDE_QUESTION_BANK.get(topic, [])
                for q_temp in bank:
                    if len(final_qs) >= 50: break
                    # Avoid duplicates
                    if any(q_temp["text"] == q.question for q in final_qs):
                         continue
                         
                    # Create in DB
                    new_q = Question(
                        type=QuestionType.APTITUDE,
                        category=q_temp["category"],
                        difficulty=DifficultyLevel.MEDIUM,
                        question=q_temp["text"],
                        options=q_temp["options"],
                        correct_answer=q_temp["correct_answer"],
                        explanation=q_temp["explanation"],
                        companies=[company_id, company_name, "zoho"],
                        is_generated=True,
                        created_by=user_id
                    )
                    await new_q.insert()
                    final_qs.append(new_q)

        # 3.5 Fallback to AI Generation ONLY if we are still critically low
        if len(final_qs) < 10:
             try:
                 # Only import and run if absolutely necessary (slow)
                 from app.services.ai_service import AIService
                 # We need some text for feedback, if no feedback exists, we can't do this
                 # For now, we rely on the bank which is already processed above
                 pass 
             except:
                 pass

        if not final_qs:
             raise HTTPException(status_code=404, detail="No aptitude questions found in database.")

        # 4. Create/Get the Assessment
        # Use a more stable title
        test_title = f"{company_id} Aptitude mock test"
        # Try to find if we already have a generated test for this company
        existing_test = await Assessment.find_one({
            "type": QuestionType.APTITUDE,
            "is_generated": True,
            "description": {"$regex": company_id} 
        })
        
        if existing_test:
            # Update questions to ensure we have the latest/best 50
            existing_test.questions = [str(q.id) for q in final_qs[:50]]
            await existing_test.save()
            return existing_test
            
        assessment = Assessment(
            title=f"Aptitude Practice Test",
            description=f"A specialized 50-question aptitude test for {company_id} based on recent patterns.",
            type=QuestionType.APTITUDE,
            questions=[str(q.id) for q in final_qs[:50]],
            duration=60,
            total_marks=len(final_qs[:50]),
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
        Dynamically generate or fetch a coding test for a company.
        """
        from app.models.company import Company, CompanyInsights
        from app.services.ai_service import AIService
        import random

        # 0. Get company info
        company = await Company.get(company_id)
        company_name = company.name.lower() if company else company_id.lower()

        # 1. Get company coding topics
        insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
        coding_topics = []
        if insights and insights.insights.important_technical_topics:
            all_text = " ".join(insights.insights.important_technical_topics)
            coding_topics = AIService._extract_coding_topics(all_text)
        
        if not coding_topics:
            coding_topics = ["arrays", "strings", "linked_list"]

        # 2. Collect Coding Questions
        search_terms = list(set([company_id, company_name]))
        
        existing_company_qs = await Question.find({
            "companies": {"$in": search_terms},
            "type": QuestionType.CODING
        }).to_list()
        
        final_qs = existing_company_qs
        
        # Priority 2: Questions matching the detected topics
        if len(final_qs) < 5:
            topic_qs = await Question.find({
                "category": {"$in": coding_topics},
                "type": QuestionType.CODING,
                "_id": {"$nin": [q.id for q in final_qs]}
            }).limit(5 - len(final_qs)).to_list()
            final_qs.extend(topic_qs)
        
        # Priority 3: Fallback from AIService Bank
        if len(final_qs) < 5:
            for topic in coding_topics:
                if len(final_qs) >= 5: break
                bank = AIService.CODING_QUESTION_BANK.get(topic, [])
                for q_temp in bank:
                    if len(final_qs) >= 5: break
                    new_q = Question(
                        type=QuestionType.CODING,
                        category=topic,
                        difficulty=q_temp["difficulty"],
                        question=q_temp["description"],
                        test_cases=q_temp["test_cases"],
                        sample_input=q_temp.get("sample_input"),
                        sample_output=q_temp.get("sample_output"),
                        companies=[company_id, company_name],
                        is_generated=True,
                        created_by=user_id,
                        correct_answer="Check test cases",
                        explanation=f"Problem: {q_temp['title']}"
                    )
                    await new_q.insert()
                    final_qs.append(new_q)

        if not final_qs:
             raise HTTPException(status_code=404, detail="No coding questions found.")

        # 3. Create/Get the Assessment
        existing_test = await Assessment.find_one({
            "type": QuestionType.CODING,
            "is_generated": True,
            "description": {"$regex": company_id} 
        })
        
        q_ids = [str(q.id) for q in final_qs[:5]]

        if existing_test:
            existing_test.questions = q_ids
            await existing_test.save()
            return existing_test
            
        assessment = Assessment(
            title=f"Coding Assessment",
            description=f"A specialized coding test for {company_id} based on recent patterns.",
            type=QuestionType.CODING,
            questions=q_ids,
            duration=90,
            total_marks=len(q_ids),
            difficulty_level=DifficultyLevel.MEDIUM,
            is_generated=True,
            created_by=user_id
        )
        await assessment.insert()
        return assessment
