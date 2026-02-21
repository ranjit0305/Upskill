import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def check_insights():
    """Check CompanyInsights using beanie"""
    from beanie import init_beanie
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.config import settings
    from app.models.company import Company, CompanyInsights, InterviewFeedback
    
    # Initialize beanie
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[Company, CompanyInsights, InterviewFeedback]
    )
    
    print("=== Checking CompanyInsights ===\n")
    
    insights_list = await CompanyInsights.find_all().to_list()
    
    if not insights_list:
        print("❌ No CompanyInsights found!")
        print("This means no feedback has been processed yet.\n")
    else:
        print(f"✅ Found {len(insights_list)} CompanyInsights\n")
        
        for idx, insight in enumerate(insights_list, 1):
            print(f"--- Insight #{idx} ---")
            print(f"Company ID: {insight.company_id}")
            print(f"Rounds: {len(insight.rounds_summary)} rounds")
            
            if insight.rounds_summary:
                for i, round_data in enumerate(insight.rounds_summary, 1):
                    print(f"  Round {i}: {round_data.name}")
                    desc = round_data.description[:100] if len(round_data.description) > 100 else round_data.description
                    print(f"    Desc: {desc}")
            else:
                print("  ⚠️ rounds_summary is EMPTY!")
            
            print(f"FAQs: {len(insight.insights.frequently_asked_questions)}")
            print(f"Topics: {insight.insights.important_technical_topics}")
            print()
    
    print("\n=== Checking InterviewFeedback ===\n")
    feedbacks = await InterviewFeedback.find_all().to_list()
    
    if not feedbacks:
        print("❌ No feedback documents found!")
    else:
        print(f"✅ Found {len(feedbacks)} feedback documents\n")
        for idx, fb in enumerate(feedbacks, 1):
            print(f"--- Feedback #{idx} ---")
            print(f"Company ID: {fb.company_id}")
            print(f"File: {fb.file_name}")
            print(f"Status: {fb.status}")
            text_len = len(fb.extracted_text or '')
            print(f"Text Length: {text_len} chars")
            if text_len > 0:
                print(f"Preview: {(fb.extracted_text or '')[:150]}...")
            print()

if __name__ == "__main__":
    asyncio.run(check_insights())
