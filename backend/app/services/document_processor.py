import fitz  # PyMuPDF
from docx import Document as DocxDocument
import os
import re
from typing import Dict, List, Any

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from PDF or Word documents using pdfplumber for better layout retention"""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if ext == ".pdf":
            import pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text(layout=True)
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                # Fallback to fitz if pdfplumber fails
                import fitz
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
