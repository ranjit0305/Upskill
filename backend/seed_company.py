import asyncio
import motor.motor_asyncio
from beanie import init_beanie, Document
from pydantic import Field, BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv

class Company(Document):
    name: str
    description: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    interview_rounds: List[str] = []
    important_areas: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "companies"

class InsightMetadata(BaseModel):
    frequently_asked_questions: List[str] = []
    important_technical_topics: List[str] = []
    coding_difficulty: str = "medium"
    common_mistakes: List[str] = []
    preparation_tips: List[str] = []

class CompanyInsights(Document):
    company_id: str
    rounds_summary: List[str] = []
    insights: InsightMetadata = Field(default_factory=InsightMetadata)
    category_mapping: Dict[str, List[str]] = {}
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "company_insights"

async def seed_company():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "upskill_db")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    await init_beanie(database=client[database_name], document_models=[Company, CompanyInsights])

    # Zoho Company Data
    zoho = Company(
        name="Zoho",
        description="Zoho Corporation is an Indian multinational technology company that makes computer software and web-based business tools.",
        website="https://www.zoho.com",
        logo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Zoho_Corporation_logo.svg/1200px-Zoho_Corporation_logo.svg.png",
        interview_rounds=["Written Test", "Programming Round 1", "Programming Round 2", "Technical Interview", "HR Interview"],
        important_areas=["Data Structures", "Algorithms", "Java/C++", "DBMS", "Core CS Topics"]
    )
    
    existing_zoho = await Company.find_one(Company.name == "Zoho")
    if not existing_zoho:
        await zoho.insert()
        company_id = str(zoho.id)
        print("Zoho company seeded.")
    else:
        company_id = str(existing_zoho.id)
        print("Zoho company already exists.")

    # Zoho Initial Insights
    zoho_insights = CompanyInsights(
        company_id=company_id,
        rounds_summary=["Round 1: Aptitude & Flowchart", "Round 2: Basic Programming", "Round 3: Advanced Programming / App Development", "Round 4: Technical HR", "Round 5: General HR"],
        insights=InsightMetadata(
            frequently_asked_questions=[
                "Explain the difference between Abstract Class and Interface.",
                "How does Garbage Collection work in Java?",
                "Reverse a linked list in groups of K.",
                "Find the middle element of a linked list.",
                "Explain ACID properties in DBMS."
            ],
            important_technical_topics=["Recursion", "Backtracking", "OOPs", "String Manipulation", "Pointers (for C/C++)"],
            coding_difficulty="hard",
            common_mistakes=[
                "Not optimizing the code for space/time complexity in Round 3.",
                "Failing to explain the logic clearly during Technical HR.",
                "Focusing too much on syntax and less on problem-solving."
            ],
            preparation_tips=[
                "Solidify your understanding of C/C++ or Java.",
                "Practice basic to medium level DS/Algo questions.",
                "Be ready for a long programming round involving building a small application or console-based system."
            ]
        ),
        category_mapping={
            "programming": ["Recursion", "Backtracking", "Arrays", "Strings"],
            "core_cs": ["OS", "DBMS", "Networking"],
            "aptitude": ["Number Series", "Profit & Loss", "Time & Work"]
        }
    )

    existing_insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)
    if not existing_insights:
        await zoho_insights.insert()
        print("Zoho insights seeded.")
    else:
        # Update existing insights to fix any validation/data issues
        existing_insights.rounds_summary = zoho_insights.rounds_summary
        existing_insights.insights = zoho_insights.insights
        existing_insights.category_mapping = zoho_insights.category_mapping
        existing_insights.last_updated = datetime.utcnow()
        await existing_insights.save()
        print("Zoho insights updated.")

if __name__ == "__main__":
    asyncio.run(seed_company())
