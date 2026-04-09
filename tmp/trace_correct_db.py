import asyncio, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def trace():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.upskill_db  # CORRECT database name
    
    print("="*60)
    print("STEP 1: All Companies")
    print("="*60)
    companies = await db.companies.find().to_list(100)
    for c in companies:
        print(f"  _id={c['_id']} | name={c.get('name','?')}")
    
    print("\n" + "="*60)
    print("STEP 2: All CompanyInsights")
    print("="*60)
    insights_list = await db.company_insights.find().to_list(100)
    if not insights_list:
        print("  >>> NO CompanyInsights documents exist! <<<")
    for ins in insights_list:
        cid = ins.get('company_id', 'MISSING')
        rounds = ins.get('rounds_summary', [])
        print(f"  company_id={cid} | rounds_count={len(rounds)}")
        for r in rounds:
            if isinstance(r, dict):
                print(f"    - {r.get('name','?')}: {str(r.get('description',''))[:80]}")
            else:
                print(f"    - (string) {r}")
    
    print("\n" + "="*60)
    print("STEP 3: DE Shaw lookup")
    print("="*60)
    target_id = "69ce88848b4677b750612d1a"
    
    # Check company
    try:
        comp = await db.companies.find_one({"_id": ObjectId(target_id)})
        print(f"  Company by ObjectId: {'FOUND - ' + comp.get('name','') if comp else 'NOT FOUND'}")
    except Exception as e:
        print(f"  Company by ObjectId: ERROR - {e}")
    
    # Check insights by string
    ins = await db.company_insights.find_one({"company_id": target_id})
    print(f"  Insights by string '{target_id}': {'FOUND' if ins else 'NOT FOUND'}")
    
    # Also search by name
    comp_name = await db.companies.find_one({"name": {"$regex": "shaw", "$options": "i"}})
    if comp_name:
        print(f"  Company by name 'shaw': FOUND - _id={comp_name['_id']} name={comp_name['name']}")
        shaw_id = str(comp_name['_id'])
        ins2 = await db.company_insights.find_one({"company_id": shaw_id})
        print(f"  Insights for shaw company_id '{shaw_id}': {'FOUND with ' + str(len(ins2.get('rounds_summary',[]))) + ' rounds' if ins2 else 'NOT FOUND'}")
    else:
        print(f"  Company by name 'shaw': NOT FOUND")

asyncio.run(trace())
