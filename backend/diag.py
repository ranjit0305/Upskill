import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "upskill_db")

async def run():
    db = AsyncIOMotorClient(URI)[DB_NAME]
    lines = []

    lines.append("== COMPANIES ==")
    for c in await db["companies"].find({}).to_list(50):
        lines.append("  id=" + str(c["_id"]) + " name=" + str(c.get("name")) + " rounds=" + str(c.get("interview_rounds", [])))

    lines.append("")
    lines.append("== INSIGHTS ==")
    docs = await db["company_insights"].find({}).to_list(50)
    if not docs:
        lines.append("  NONE")
    for d in docs:
        rs = d.get("rounds_summary", [])
        lines.append("  company_id=" + str(d.get("company_id")) + " | rounds_count=" + str(len(rs)))
        for r in rs:
            lines.append("    [" + str(r.get("name")) + "] " + str(r.get("description", ""))[:80])

    lines.append("")
    lines.append("== FEEDBACKS ==")
    fbs = await db["interview_feedback"].find({}).to_list(50)
    if not fbs:
        lines.append("  NONE")
    for f in fbs:
        t = f.get("extracted_text", "") or ""
        lines.append("  cid=" + str(f.get("company_id")) + " file=" + str(f.get("file_name")) + " status=" + str(f.get("status")) + " textlen=" + str(len(t)))

    with open("diag.txt", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    print("Done. Written to diag.txt")

asyncio.run(run())
