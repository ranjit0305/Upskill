from app.services.judge0_service import Judge0Service
from app.models.assessment import Question, Answer
import logging

logger = logging.getLogger(__name__)

class CodingService:
    """Service to handle coding question evaluation"""
    
    @staticmethod
    async def evaluate_coding_answer(
        question: Question,
        code: str,
        language: str,
        time_taken: int
    ) -> Answer:
        """Evaluate a coding answer against its test cases"""
        
        test_cases = question.test_cases or []
        if not test_cases:
            # If no test cases, we can't evaluate automatically. 
            # For now, mark as passed if it compiles/runs? Or just return neutral.
            return Answer(
                question_id=str(question.id),
                code=code,
                language=language,
                is_correct=True,
                time_taken=time_taken,
                test_results=[]
            )

        # Run test cases
        results = await Judge0Service.run_test_cases(code, language, test_cases)
        
        evaluated_results = []
        passed_count = 0
        
        for i, res in enumerate(results):
            # Judge0 status 3 is "Accepted"
            is_passed = res.get("status", {}).get("id") == 3
            if is_passed:
                passed_count += 1
            
            evaluated_results.append({
                "test_case_index": i,
                "status": res.get("status", {}).get("description"),
                "passed": is_passed,
                "stdout": res.get("stdout"),
                "stderr": res.get("stderr"),
                "time": res.get("time"),
                "memory": res.get("memory")
            })

        is_all_passed = passed_count == len(test_cases)
        
        # Calculate score (percentage of test cases passed)
        # We store is_correct as True if ALL pass, but we can also store partial credit logic elsewhere.
        
        return Answer(
            question_id=str(question.id),
            code=code,
            language=language,
            is_correct=is_all_passed,
            time_taken=time_taken,
            test_results=evaluated_results
        )

    @staticmethod
    def calculate_coding_points(answer: Answer) -> float:
        """Calculate points for a coding answer based on test cases"""
        if not answer.test_results:
            return 1.0 if answer.is_correct else 0.0
            
        total_tc = len(answer.test_results)
        passed_tc = sum(1 for tc in answer.test_results if tc.get("passed"))
        
        return passed_tc / total_tc if total_tc > 0 else 0.0
