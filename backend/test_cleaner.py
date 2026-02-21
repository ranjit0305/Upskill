import sys
import os

# Mock settings to avoid import errors if env is missing
import os
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "test_db"
os.environ["SECRET_KEY"] = "test_secret"

from app.services.ai_service import AIService

def test_clean_round_description():
    dirty_text = """
    Round details: Round 1
    Platform: HackerRank
    Your Comments: The questions were medium level.
    Details about Questions on Coding round:
    1. Two sum problem.
    2. Dynamic programming.
    """
    
    expected_clean = "The questions were medium level. 1. Two sum problem. 2. Dynamic programming."
    
    cleaned = AIService._clean_round_description(dirty_text)
    print(f"Dirty:\n{dirty_text}")
    print(f"Cleaned:\n'{cleaned}'")
    
    # Check if noise is removed
    assert "Platform" not in cleaned
    assert "Your Comments" not in cleaned
    assert "Round details" not in cleaned
    print("✅ Cleaning test passed!")

def test_overlap():
    t1 = "The quick brown fox jumps over the lazy dog."
    t2 = "Quick brown fox jumps over lazy dog."
    t3 = "Arbitrary text about algorithms."
    
    score1 = AIService._calculate_overlap(t1, t2)
    print(f"Overlap (Similar): {score1:.2f}")
    assert score1 > 0.8
    
    score2 = AIService._calculate_overlap(t1, t3)
    print(f"Overlap (Different): {score2:.2f}")
    assert score2 < 0.2
    
    print("✅ Overlap test passed!")

if __name__ == "__main__":
    test_clean_round_description()
    test_overlap()
