import fitz  # PyMuPDF
from docx import Document as DocxDocument
import os
import re
from typing import Dict, List, Any

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from PDF or Word documents"""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if ext == ".pdf":
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
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
