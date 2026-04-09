import fitz  # PyMuPDF
from docx import Document as DocxDocument
import os
import re
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from PDF or Word documents using pdfplumber for better layout retention"""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text(layout=True)
                        if page_text:
                            text += page_text + "\n"
            except ModuleNotFoundError:
                logger.warning("pdfplumber not installed; falling back to PyMuPDF for %s", file_path)
            except Exception as e:
                logger.warning("pdfplumber failed for %s, falling back to PyMuPDF: %s", file_path, e)

            if not text.strip():
                doc = fitz.open(file_path)
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text += page_text + "\n"
                doc.close()
        elif ext in [".docx", ".doc"]:
            doc = DocxDocument(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"

        return text

    @staticmethod
    async def process_insights(text: str) -> Dict[str, Any]:
        """
        Extract basic insights from text using AI Service.
        """
        from app.services.ai_service import AIService
        return await AIService.analyze_feedback(text)
