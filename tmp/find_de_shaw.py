import asyncio, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from motor.motor_asyncio import AsyncIOMotorClient

async def find_de_shaw():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.upskill
    
    # Check ALL collections
    collections = await db.list_collection_names()
    print(f"All collections: {collections}")
    
    # Search for 'Shaw' in every collection
    for coll_name in collections:
        coll = db[coll_name]
        # Try text search
        docs = await coll.find({}).to_list(100)
        for doc in docs:
            doc_str = str(doc)
            if 'shaw' in doc_str.lower() or 'de shaw' in doc_str.lower() or 'DE Shaw' in doc_str:
                print(f"\nFOUND 'shaw' in collection '{coll_name}':")
                print(f"  _id={doc.get('_id')}")
                # Print relevant fields
                for k in ['name', 'company_id', 'company_name', 'company']:
                    if k in doc:
                        print(f"  {k}={doc[k]}")
                break
    
    # Also look for that exact ID fragment
    for coll_name in collections:
        coll = db[coll_name]
        docs = await coll.find({}).to_list(100)
        for doc in docs:
            doc_str = str(doc)
            if '69ce8884' in doc_str:
                print(f"\nFOUND '69ce8884' in collection '{coll_name}':")
                print(f"  _id={doc.get('_id')}")
                for k in ['name', 'company_id', 'company_name']:
                    if k in doc:
                        print(f"  {k}={doc[k]}")

asyncio.run(find_de_shaw())
