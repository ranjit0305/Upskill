import requests
import json

BASE_URL = "http://localhost:8000"

def test_dashboard_api():
    """Test the company dashboard API to see what data is returned"""
    
    # First, get list of companies to find Zoho's ID
    print("=== Fetching Companies ===")
    response = requests.get(f"{BASE_URL}/companies")
    
    if response.status_code != 200:
        print(f"❌ Failed to get companies: {response.status_code}")
        return
    
    companies = response.json()
    print(f"Found {len(companies)} companies\n")
    
    # Find Zoho
    zoho = None
    for company in companies:
        if 'zoho' in company['name'].lower():
            zoho = company
            break
    
    if not zoho:
        print("❌ Zoho company not found!")
        print("Available companies:")
        for c in companies:
            print(f"  - {c['name']} (ID: {c['_id']})")
        return
    
    print(f"✅ Found Zoho: {zoho['name']}")
    print(f"   ID: {zoho['_id']}\n")
    
    # Now get the dashboard
    print("=== Fetching Dashboard Data ===")
    
    # We need a user_id - let's use a dummy one for testing
    test_user_id = "000000000000000000000001"
    
    response = requests.get(
        f"{BASE_URL}/companies/{zoho['_id']}/dashboard",
        params={"user_id": test_user_id}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get dashboard: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    data = response.json()
    
    print("✅ Dashboard data retrieved!\n")
    print("=== Insights Data ===")
    
    if data.get('insights'):
        insights = data['insights']
        print(f"Insights object exists: YES")
        print(f"Rounds summary: {insights.get('rounds_summary', 'NOT FOUND')}")
        
        if insights.get('rounds_summary'):
            rounds = insights['rounds_summary']
            print(f"\n✅ Found {len(rounds)} rounds:")
            for i, round_data in enumerate(rounds, 1):
                print(f"\n  Round {i}:")
                print(f"    Name: {round_data.get('name', 'N/A')}")
                desc = round_data.get('description', 'N/A')
                print(f"    Description: {desc[:100]}..." if len(desc) > 100 else f"    Description: {desc}")
        else:
            print("\n❌ rounds_summary is EMPTY or NULL!")
            print(f"   Full insights object: {json.dumps(insights, indent=2)}")
    else:
        print("❌ No insights object in response!")
        print(f"\nFull response keys: {list(data.keys())}")
    
    print("\n=== Other Dashboard Data ===")
    print(f"Readiness Score: {data.get('readiness_score', 'N/A')}")
    print(f"Learning Path Items: {len(data.get('learning_path', []))}")
    print(f"Generated Questions: {len(data.get('generated_questions', []))}")

if __name__ == "__main__":
    test_dashboard_api()
