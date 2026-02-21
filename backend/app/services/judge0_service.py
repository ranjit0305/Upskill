import httpx
import base64
from typing import List, Dict, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class Judge0Service:
    """Service to interact with Judge0 API (Free Public Instance)"""
    
    # Official Public Community Instance - No Key Required
    BASE_URL = "https://ce.judge0.com"
    API_KEY = None
    API_HOST = None
    
    LANGUAGE_MAP = {
        "python": 71,   # Python 3
        "java": 62,     # Java 11 (Standard for placement)
        "cpp": 54,      # C++ 17
        "javascript": 63, # Node.js 12
        "c": 50         # C (GCC 9.2.0)
    }

    @classmethod
    async def execute_code(
        cls, 
        source_code: str, 
        language: str, 
        stdin: Optional[str] = None,
        expected_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit code to Public Judge0 API for execution"""
        
        language_id = cls.LANGUAGE_MAP.get(language.lower(), 71) # Default to Python
        
        # Base64 encode for safety
        payload = {
            "source_code": base64.b64encode(source_code.encode()).decode(),
            "language_id": language_id,
            "stdin": base64.b64encode(stdin.encode()).decode() if stdin else None,
            "expected_output": base64.b64encode(expected_output.encode()).decode() if expected_output else None
        }

        async with httpx.AsyncClient() as client:
            try:
                # Use public endpoint directly without RapidAPI headers
                response = await client.post(
                    f"{cls.BASE_URL}/submissions?base64_encoded=true&wait=true",
                    json=payload,
                    timeout=15.0
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Judge0 execution failed: {response.text}")
                    return {"status": {"id": 0, "description": "Execution Error"}, "message": response.text}

                result = response.json()
                
                # Base64 decode the output fields if they exist
                for field in ["stdout", "stderr", "compile_output", "message"]: # Added 'message' to the loop
                    if result.get(field):
                        try:
                            result[field] = base64.b64decode(result[field]).decode('utf-8')
                        except Exception:
                            # Log error but continue if decoding fails for a specific field
                            logger.warning(f"Failed to decode Judge0 field '{field}': {result[field]}")
                            pass
                            
                return result

            except Exception as e:
                logger.error(f"Error calling Judge0: {e}")
                return {"status": {"id": 0, "description": "Internal Error"}, "message": str(e)}

    @classmethod
    async def run_test_cases(
        cls, 
        source_code: str, 
        language: str, 
        test_cases: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Run multiple test cases concurrently"""
        import asyncio
        
        tasks = [
            cls.execute_code(source_code, language, tc.get("input"), tc.get("output"))
            for tc in test_cases
        ]
        
        results = await asyncio.gather(*tasks)
        return results
