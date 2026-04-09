"""
Trace the FULL end-to-end flow for DE Shaw dashboard:
1. Check what's in Company collection
2. Check what's in CompanyInsights collection  
3. Check if company_id format matches
4. Simulate the dashboard API call
"""
import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def trace():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.upskill
    await init_beanie(database=db, document_models=[])  # skip beanie models
    
    # 1. Raw MongoDB query - list ALL companies
    print("=" * 60)
    print("STEP 1: All Companies in DB")
    print("=" * 60)
    companies = await db.companies.find().to_list(100)
    for c in companies:
        print(f"  _id={c['_id']} | type={type(c['_id'])} | name={c.get('name','?')}")
    
    # 2. Raw MongoDB query - list ALL company_insights
    print("\n" + "=" * 60)
    print("STEP 2: All CompanyInsights in DB")
    print("=" * 60)
    insights_list = await db.company_insights.find().to_list(100)
    if not insights_list:
        print("  >>> NO CompanyInsights documents exist at all! <<<")
    for ins in insights_list:
        cid = ins.get('company_id', 'MISSING')
        rounds = ins.get('rounds_summary', [])
        print(f"  company_id={cid} | type={type(cid)} | rounds_count={len(rounds)}")
        for r in rounds:
            print(f"    - {r.get('name','?')}: {str(r.get('description',''))[:80]}")
    
    # 3. Check the specific DE Shaw company
    print("\n" + "=" * 60)
    print("STEP 3: DE Shaw specific lookup")
    print("=" * 60)
    target_id = "69ce88848b4677b750612d1a"
    
    # Try finding by string
    ins_str = await db.company_insights.find_one({"company_id": target_id})
    print(f"  Find by string '{target_id}': {'FOUND' if ins_str else 'NOT FOUND'}")
    
    # Try finding by ObjectId
    from bson import ObjectId
    try:
        ins_oid = await db.company_insights.find_one({"company_id": ObjectId(target_id)})
        print(f"  Find by ObjectId: {'FOUND' if ins_oid else 'NOT FOUND'}")
    except:
        print(f"  Find by ObjectId: INVALID ID")
    
    # Check company exists
    comp = await db.companies.find_one({"_id": ObjectId(target_id)})
    print(f"  Company doc exists: {'YES - ' + comp.get('name','') if comp else 'NO'}")
    
    # 4. Check what the dashboard service would return
    print("\n" + "=" * 60)
    print("STEP 4: Simulate Dashboard API")
    print("=" * 60)
    
    from app.models.company import Company, CompanyInsights
    from app.models.performance import Performance, ReadinessScore
    from app.models.assessment import Question, Submission
    from app.models.user import User
    
    await init_beanie(database=db, document_models=[Company, CompanyInsights, Performance, ReadinessScore, Question, Submission, User])
    
    # This is what CompanyService.get_company_prep_dashboard does
    from beanie import PydanticObjectId
    lookup_id = PydanticObjectId(target_id)
    company = await Company.get(lookup_id)
    print(f"  Beanie Company.get: {'FOUND - ' + company.name if company else 'NOT FOUND'}")
    
    if company:
        company_id_str = str(company.id)
        print(f"  company.id as string: '{company_id_str}'")
        
        insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id_str)
        print(f"  CompanyInsights.find_one(company_id == '{company_id_str}'): {'FOUND' if insights else 'NOT FOUND'}")
        
        if insights:
            print(f"    rounds_summary count: {len(insights.rounds_summary)}")
            for r in insights.rounds_summary:
                print(f"    - {r.name}: {r.description[:80]}...")
            print(f"    FAQs: {len(insights.insights.frequently_asked_questions)}")
            print(f"    Topics: {len(insights.insights.important_technical_topics)}")
        else:
            # Try alternate lookups
            all_insights = await CompanyInsights.find_all().to_list()
            print(f"  Total CompanyInsights docs (Beanie): {len(all_insights)}")
            for ai in all_insights:
                print(f"    company_id='{ai.company_id}' (type={type(ai.company_id)})")

asyncio.run(trace())
