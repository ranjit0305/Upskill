import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MLService:
    _qa_pipeline = None

    @classmethod
    def get_pipeline(cls):
        if cls._qa_pipeline is None:
            from transformers import pipeline
            logger.info("Loading DistilBERT QA model...")
            try:
                cls._qa_pipeline = pipeline(
                    "question-answering", 
                    model="distilbert-base-cased-distilled-squad",
                    tokenizer="distilbert-base-cased-distilled-squad"
                )
                logger.info("DistilBERT model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                raise e
        return cls._qa_pipeline

    @staticmethod
    def answer_question(context: str, question: str) -> Dict[str, Any]:
        """
        Ask a question to the context using the loaded model.
        """
        if not context or not question:
            return {"answer": "", "score": 0.0}
            
        nlp = MLService.get_pipeline()
        
        # QA models have a limit on token length (usually 512). 
        # For a simple implementation, we might need to truncate or chunk.
        # Here we truncate context to ~2000 chars as a rough proxy for tokens to avoid crashes.
        # A more robust solution would use sliding windows.
        truncated_context = context[:2000] 
        
        try:
            result = nlp(question=question, context=truncated_context)
            return result
        except Exception as e:
            logger.warning(f"QA inference failed: {e}")
            return {"answer": "", "score": 0.0}
