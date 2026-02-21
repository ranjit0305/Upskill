import asyncio
import sys
import os

# Add the current directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services.piston_service import PistonService

async def test_piston():
    print("--- Testing PistonService ---")
    
    # Test 1: Simple execution
    print("\nTest 1: Simple Python Execution")
    code = "print('Hello from Piston!')"
    result = await PistonService.execute_code(code, "python")
    print(f"Status: {result['status']['description']}")
    print(f"Stdout: {result['stdout']}")
    
    # Test 2: Java Execution
    print("\nTest 2: Simple Java Execution")
    java_code = """
public class Solution {
    public static void main(String[] args) {
        System.out.println("Java is running!");
    }
}
"""
    result = await PistonService.execute_code(java_code, "java")
    print(f"Status: {result['status']['description']}")
    print(f"Stdout: {result['stdout']}")
    
    # Test 3: Test cases
    print("\nTest 3: Multiple Test Cases (Python)")
    sum_code = "import sys; x = int(input()); y = int(input()); print(x+y)"
    test_cases = [
        {"input": "2\n3", "output": "5"},
        {"input": "10\n20", "output": "30"},
        {"input": "5\n5", "output": "11"} # This should fail
    ]
    results = await PistonService.run_test_cases(sum_code, "python", test_cases)
    
    for i, res in enumerate(results):
        print(f"TestCase {i}: Status={res['status']['description']}, Stdout={res.get('stdout', '').strip()}")

if __name__ == "__main__":
    asyncio.run(test_piston())
