import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_company():
    print("Testing Create Company API...")
    
    # Randomize name to avoid conflict
    import random
    rand_id = random.randint(1000, 9999)
    company_data = {
        "name": f"Test Company {rand_id}",
        "description": "A test company created by verification script.",
        "logo_url": "https://via.placeholder.com/150",
        "website": "https://example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/companies", json=company_data)
        
        if response.status_code == 201:
            print("✅ Company created successfully!")
            print(f"Response: {response.json()}")
        elif response.status_code == 400:
             print(f"⚠️ Company already exists (Expected if running multiple times).")
        else:
            print(f"❌ Failed to create company. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_create_company()
