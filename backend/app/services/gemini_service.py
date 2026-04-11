import logging
from typing import Dict, Any, List
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

class GeminiEvaluator:
    """
    Evaluator that uses semantic analysis to score interview answers.
    While named 'Gemini' for the premium feel, it currently uses DeBERTa/DistilBERT 
    on-device pipelines via MLService to ensure zero-latency and offline working.
    """

    @staticmethod
    def evaluate_semantic_fit(question: str, answer: str, expected_points: List[str]) -> Dict[str, Any]:
        """
        Evaluate how well the answer covers the expected technical/HR points.
        """
        if not answer or len(answer.split()) < 5:
            return {
                "score": 10.0,
                "strengths": [],
                "improvements": ["The answer is too short to evaluate. Please provide more detail."],
                "coverage": 0
            }

        strengths = []
        improvements = []
        coverage_count = 0
        
        # Candidate labels for zero-shot classification to check coverage of points
        for point in expected_points:
            # We ask: does the 'answer' contain the concept of 'point'?
            classification = MLService.classify_text(answer, [point, "unrelated information"])
            if classification["labels"] and classification["labels"][0] == point and classification["scores"][0] > 0.6:
                coverage_count += 1
                strengths.append(f"Successfully covered the point: {point}")
            else:
                improvements.append(f"Try to elaborate more on: {point}")

        coverage_score = (coverage_count / len(expected_points)) * 100 if expected_points else 100
        
        # Use QA pipeline to extract a "clarity" score
        qa_check = MLService.answer_question(answer, "What is the main point of this response?")
        clarity_score = qa_check["score"] * 100
        
        # Final semantic score
        semantic_score = (coverage_score * 0.7) + (clarity_score * 0.3)
        
        return {
            "score": round(semantic_score, 2),
            "strengths": strengths[:2],
            "improvements": improvements[:2],
            "coverage": coverage_score
        }

    @staticmethod
    def get_structured_feedback(category: str, score: float) -> str:
        """Get a human-like feedback summary based on score and category."""
        if score > 80:
            return f"Excellent {category} response. You demonstrated deep understanding and structured your thoughts effectively."
        elif score > 60:
            return f"Good {category} answer. You covered the essentials but can add more specific examples or technical depth."
        else:
            return f"Your {category} response needs more detail. Focus on staying structured and covering all expected technical points."
