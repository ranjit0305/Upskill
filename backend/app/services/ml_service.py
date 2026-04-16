import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MLService:
    _qa_pipeline = None
    _classification_pipeline = None

    @classmethod
    def get_qa_pipeline(cls):
        if cls._qa_pipeline is None:
            from transformers import pipeline
            logger.info("Loading DistilBERT QA model...")
            try:
                cls._qa_pipeline = pipeline(
                    "question-answering", 
                    model="distilbert-base-cased-distilled-squad",
                    tokenizer="distilbert-base-cased-distilled-squad",
                    use_fast=False
                )
                logger.info("DistilBERT model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                raise e
        return cls._qa_pipeline

    @classmethod
    def get_classification_pipeline(cls):
        if cls._classification_pipeline is None:
            from transformers import pipeline
            logger.info("Loading DeBERTa Zero-Shot Classification model...")
            try:
                cls._classification_pipeline = pipeline(
                    "zero-shot-classification",
                    model="cross-encoder/nli-deberta-v3-small",
                    use_fast=False
                )
                logger.info("DeBERTa Classification model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load classification model: {e}")
                raise e
        return cls._classification_pipeline

    @staticmethod
    def answer_question(context: str, question: str) -> Dict[str, Any]:
        """
        Ask a question to the context using the loaded model.
        """
        if not context or not question:
            return {"answer": "", "score": 0.0}
            
        nlp = MLService.get_qa_pipeline()
        truncated_context = context[:2000] 
        
        try:
            result = nlp(question=question, context=truncated_context)
            return result
        except Exception as e:
            logger.warning(f"QA inference failed: {e}")
            return {"answer": "", "score": 0.0}

    @staticmethod
    def classify_text(text: str, candidate_labels: List[str]) -> Dict[str, Any]:
        """
        Classify text against multiple labels using zero-shot classification.
        """
        if not text or not candidate_labels:
            return {"labels": [], "scores": []}
            
        classifier = MLService.get_classification_pipeline()
        try:
            result = classifier(text, candidate_labels)
            return result
        except Exception as e:
            logger.warning(f"Classification failed: {e}")
            return {"labels": [], "scores": []}
