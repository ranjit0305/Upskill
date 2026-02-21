import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PistonService:
    """Service to interact with Piston Code Execution API (Free/No-Key)"""
    
    BASE_URL = "https://emkc.org/api/v2/piston"
    
    # Map for Piston runtimes
    LANGUAGE_MAP = {
        "python": {"language": "python", "version": "3.10.0"},
        "java": {"language": "java", "version": "15.0.2"},
        "cpp": {"language": "c++", "version": "10.2.0"},
        "javascript": {"language": "javascript", "version": "18.15.0"},
        "c": {"language": "c", "version": "10.2.0"}
    }

    @classmethod
    async def execute_code(
        cls, 
        source_code: str, 
        language: str, 
        stdin: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit code to Piston API for execution"""
        
        lang_info = cls.LANGUAGE_MAP.get(language.lower(), cls.LANGUAGE_MAP["python"])
        
        payload = {
            "language": lang_info["language"],
            "version": lang_info["version"],
            "files": [
                {
                    "content": source_code
                }
            ],
            "stdin": stdin or ""
        }
        
        print(f"DEBUG: Piston Payload: {payload}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{cls.BASE_URL}/execute",
                    json=payload,
                    timeout=15.0
                )
                
                print(f"DEBUG: Piston Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"DEBUG: Piston Error Response: {response.text}")
                    logger.error(f"Piston execution failed: {response.text}")
                    return {
                        "status": {"id": 0, "description": "Execution Error"},
                        "message": f"API Error {response.status_code}: {response.text}",
                        "stdout": "",
                        "stderr": response.text,
                        "compile_output": None
                    }

                result = response.json()
                print(f"DEBUG: Piston Result: {result}")
                run = result.get("run", {})
                
                # Transform to a structure similar to Judge0 for compatibility
                status_id = 3 # Default to "Accepted" if it ran
                if run.get("code") != 0:
                    status_id = 4 # "Runtime Error"
                if run.get("stderr"):
                    # If there's stderr but code is 0, might still be okay, 
                    # but if it failed, it's definitely not 3.
                    pass

                return {
                    "status": {
                        "id": status_id,
                        "description": "Accepted" if status_id == 3 else "Runtime Error"
                    },
                    "stdout": run.get("stdout"),
                    "stderr": run.get("stderr"),
                    "compile_output": result.get("compile", {}).get("stderr") if result.get("compile") else None,
                    "time": None, # Piston doesn't return time per se in the same way
                    "memory": None
                }

            except Exception as e:
                logger.error(f"Error calling Piston: {e}")
                return {"status": {"id": 0, "description": "Internal Error"}, "message": str(e)}

    @classmethod
    async def run_test_cases(
        cls, 
        source_code: str, 
        language: str, 
        test_cases: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Run multiple test cases against Piston"""
        import asyncio
        
        tasks = [
            cls.execute_code(source_code, language, tc.get("input"))
            for tc in test_cases
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Post-process for "expected output" check (Judge0 does this server-side, Piston doesn't)
        for i, res in enumerate(results):
            expected = test_cases[i].get("output", "").strip()
            actual = (res.get("stdout") or "").strip()
            
            if res["status"]["id"] == 3: # If it ran successfully
                if actual != expected:
                    res["status"]["id"] = 4 # Mismatch
                    res["status"]["description"] = "Wrong Answer"
            
        return results
