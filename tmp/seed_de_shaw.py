"""Create initial CompanyInsights for DE Shaw with sample round data"""
import asyncio, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.company import Company, CompanyInsights, InsightMetadata, RoundDetail
from app.models.user import User
from app.models.assessment import Question, Submission
from app.models.performance import Performance, ReadinessScore

async def seed_de_shaw_insights():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.upskill_db,
        document_models=[Company, CompanyInsights, User, Question, Submission, Performance, ReadinessScore]
    )

    company_id = "69ce88848b4677b750612d1a"
    company = await Company.get(company_id)
    if not company:
        print("DE Shaw company not found!")
        return
    
    print(f"Found company: {company.name} (id={company.id})")
    
    # Check if insights already exist
    existing = await CompanyInsights.find_one(CompanyInsights.company_id == str(company.id))
    if existing:
        print(f"Insights already exist with {len(existing.rounds_summary)} rounds")
        return
    
    # Create initial insights for DE Shaw
    insights = CompanyInsights(
        company_id=str(company.id),
        rounds_summary=[
            RoundDetail(
                name="Online Assessment",
                description="The Online Assessment at DE Shaw typically includes aptitude questions covering quantitative ability, logical reasoning, and verbal ability, along with 2-3 coding problems focused on data structures and algorithms."
            ),
            RoundDetail(
                name="Technical Interview 1", 
                description="The first technical interview focuses on core CS fundamentals including Data Structures, Algorithms, OOP concepts, and DBMS. Candidates are expected to solve coding problems on a whiteboard or shared editor."
            ),
            RoundDetail(
                name="Technical Interview 2",
                description="The second technical round dives deeper into System Design, problem-solving, and project discussions. Interviewers may ask puzzles and brain teasers alongside technical questions."
            ),
            RoundDetail(
                name="HR Interview",
                description="The HR round covers behavioral questions, salary expectations, and cultural fit. Common topics include 'Why DE Shaw?', relocation preferences, and career goals."
            )
        ],
        insights=InsightMetadata(
            frequently_asked_questions=[
                "What is the difference between a process and a thread?",
                "Explain the ACID properties in DBMS.",
                "How does a HashMap work internally in Java?",
                "What is dynamic programming? Give an example.",
                "Explain the concept of deadlock in Operating Systems."
            ],
            important_technical_topics=["Data Structures", "Algorithms", "System Design", "DBMS", "OOP"],
            coding_difficulty="hard",
            common_mistakes=[
                "Not optimizing solutions for time/space complexity.",
                "Failing to clarify problem constraints before coding.",
                "Ignoring edge cases in coding problems."
            ],
            preparation_tips=[
                "Focus on medium to hard LeetCode problems, especially DP and Graphs.",
                "Brush up on System Design fundamentals for the second technical round.",
                "Be ready to discuss your resume projects in depth."
            ]
        )
    )
    
    await insights.insert()
    print(f"Successfully seeded DE Shaw insights with {len(insights.rounds_summary)} rounds!")
    
    # Verify
    check = await CompanyInsights.find_one(CompanyInsights.company_id == str(company.id))
    print(f"Verification: Found {len(check.rounds_summary)} rounds for DE Shaw")
    for r in check.rounds_summary:
        print(f"  - {r.name}: {r.description[:60]}...")

asyncio.run(seed_de_shaw_insights())
