import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['upskill_db']
company = db['companies'].find_one()
company_id = str(company['_id'])
# Clear stale technical questions from insights
result = db['company_insights'].update_one(
    {'company_id': company_id},
    {'$set': {'insights.technical_questions': [], 'insights.frequently_asked_questions': []}}
)
print(f"Cleared stale data for company: {company['name']} ({company_id}). Modified: {result.modified_count}")
