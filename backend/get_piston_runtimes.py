import httpx
import json

def get_runtimes():
    response = httpx.get("https://emkc.org/api/v2/piston/runtimes")
    runtimes = response.json()
    for r in runtimes:
        print(f"{r['language']} ({r['version']})")

if __name__ == "__main__":
    get_runtimes()
