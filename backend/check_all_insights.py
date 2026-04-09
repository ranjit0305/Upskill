import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "upskill_db")

async def check():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]

    print("\n===== COMPANIES =====")
    companies = await db["companies"].find({}).to_list(100)
    for c in companies:
        print(f"  ID: {c['_id']}  Name: {c.get('name')}  Rounds: {c.get('interview_rounds', [])}")

    print("\n===== COMPANY INSIGHTS =====")
    insights = await db["company_insights"].find({}).to_list(100)
    if not insights:
        print("  [NO RECORDS FOUND]")
    for ins in insights:
        rounds = ins.get("rounds_summary", [])
        print(f"  company_id: {ins.get('company_id')}")
        print(f"  rounds_summary count: {len(rounds)}")
        for r in rounds:
            print(f"    - {r.get('name')}: {r.get('description','')[:80]}...")
        print()

    print("\n===== INTERVIEW FEEDBACKS =====")
    feedbacks = await db["interview_feedback"].find({}).to_list(100)
    if not feedbacks:
        print("  [NO FEEDBACKS UPLOADED]")
    for fb in feedbacks:
        has_text = bool(fb.get("extracted_text", "").strip())
        print(f"  company_id: {fb.get('company_id')}  file: {fb.get('file_name')}  status: {fb.get('status')}  has_text: {has_text}")

    client.close()

asyncio.run(check())
