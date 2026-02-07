import requests
import sys

BASE_URL = "http://localhost:8000"

def test_flow():
    email = f"testuser_{int(time.time())}@example.com" if "time" in globals() else "testuser_99@example.com"
    import time
    email = f"testuser_{int(time.time())}@example.com"
    password = "password123"
    
    print(f"--- testing registration for {email} ---")
    reg_data = {
        "email": email,
        "password": password,
        "role": "student",
        "profile": {"name": "Test User"}
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
        print(f"Registration Status: {r.status_code}")
        print(f"Registration Body: {r.text}")
        
        if r.status_code in [201, 400]: # 400 might mean already exists
            print(f"--- testing login for {email} ---")
            login_data = {
                "email": email,
                "password": password
            }
            l = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            print(f"Login Status: {l.status_code}")
            print(f"Login Body: {l.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_flow()
