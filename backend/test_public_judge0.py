import httpx
import asyncio
import base64

async def test_public_judge0():
    print("--- Testing Public Judge0 (ce.judge0.com) ---")
    
    url = "https://ce.judge0.com/submissions?base64_encoded=true&wait=true"
    
    source_code = "print('Hello from Public Judge0!')"
    payload = {
        "source_code": base64.b64encode(source_code.encode()).decode(),
        "language_id": 71 # Python 3
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=15.0)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 201 or response.status_code == 200:
                print("Success!")
                print(f"Result: {response.json()}")
            else:
                print(f"Failed: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_public_judge0())
