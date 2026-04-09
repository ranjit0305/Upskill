import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.models.user import User
from app.models.assessment import Question
from app.services.document_processor import DocumentProcessor
from app.routers.company import upload_feedback

async def simulate_upload():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["upskill_db"]
    await init_beanie(database=db, document_models=[Company, CompanyInsights, InterviewFeedback, User, Question])
    
    # Check for DE Shaw company
    companies = await Company.find().to_list()
    de_shaw = None
    for c in companies:
        if "shaw" in c.name.lower():
            de_shaw = c
            break
            
    if not de_shaw:
        print("DE Shaw not found!")
        return
        
    print(f"Testing for company: {de_shaw.name} (id={de_shaw.id})")
    
    # Get an admin user
    user_id = "mock_admin_id"
    print(f"Using uploader: {user_id}")
    
    # Instead of creating a PDF, just use a sample extracted text
    text = """
    DE Shaw Interview Experience
    Round 1: Online Assessment
    The test had 15 aptitude questions on time and work, profit and loss.
    There were 2 coding questions. One on dynamic programming and one on arrays.
     Round 2: Technical Interview
    They asked me to reverse a linked list and explain ACID properties in DBMS.
    """
    
    print("Extracted text length:", len(text))
    
    raw_insights = await DocumentProcessor.process_insights(text)
    print("Raw Insights keys:", raw_insights.keys())
    print("Rounds found:", len(raw_insights.get("rounds", [])))
    print("Tech Qs found:", len(raw_insights.get("technical_questions", [])))
    
    # Questions generation
    from app.services.ai_service import AIService
    generated_questions = await AIService.generate_questions_from_feedback(text, str(de_shaw.id), str(user_id))
    print("Generated questions:", len(generated_questions))

asyncio.run(simulate_upload())
