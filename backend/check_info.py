import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def r():
    db = AsyncIOMotorClient(settings.MONGODB_URI)[settings.DATABASE_NAME]
    comps = await db.Company.find({}).to_list(100)
    for c in comps:
        cid = str(c['_id'])
        print(f"Company: {c.get('name', 'Unknown')}, ID: {cid}")
        fbs = await db.InterviewFeedback.count_documents({"company_id": cid})
        qs = await db.Question.count_documents({"companies": cid})
        insights = await db.CompanyInsights.find_one({"company_id": cid})
        rs = len(insights.get("rounds_summary", [])) if insights else 0
        print(f"  Feedbacks: {fbs}, Questions: {qs}, Rounds: {rs}")

if __name__ == "__main__":
    asyncio.run(r())
