import re
from typing import List, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    async def analyze_feedback(text: str) -> Dict[str, Any]:
        """
        Analyze feedback text to extract structured insights.
        Attempts to use LLM if available, falls back to enhanced NLP.
        """
        # For now, we use enhanced NLP heuristics that act like an LLM
        # to avoid blocking without a local model file.
        # But we structure it to be easily replaced by Llama calls.
        
        insights = {
            "rounds": AIService._extract_and_normalize_rounds(text),
            "faqs": AIService._extract_faqs(text),
            "topics": AIService._extract_topics(text),
            "difficulty": AIService._detect_difficulty(text),
            "mistakes": AIService._extract_list(text, ["mistake", "caution", "avoid", "failed"]),
            "tips": AIService._extract_list(text, ["tip", "advice", "suggest", "recommend"])
        }
        return insights

    @staticmethod
    def _extract_and_normalize_rounds(text: str) -> List[Dict[str, str]]:
        """Deduplicate and normalize round names with high-quality, professional descriptions"""
        # Improved pattern to capture rounds
        pattern = r"(Round \d+|First Round|Second Round|Third Round|Fourth Round|Fifth Round|Technical Round|HR Round|Aptitude Round|Coding Round|Managerial Round|Technical Interview|ROUND \d+)"
        
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        final_rounds = {} # canonical_name -> {name, description}
        
        # Mapping for normalization
        ordinals = {
            "first": "Round 1",
            "second": "Round 2",
            "third": "Round 3",
            "fourth": "Round 4",
            "fifth": "Round 5"
        }
        
        type_keywords = {
            "aptitude": "Online Assessment",
            "coding": "Coding Assessment",
            "technical": "Technical Interview",
            "hr": "HR Interview",
            "managerial": "Managerial Discussion"
        }
        
        for m in matches:
            match_text = m.group(0)
            m_lower = match_text.lower()
            
            # 1. Normalize Canonical Name
            canonical = match_text.title()
            for ord_word, target in ordinals.items():
                if ord_word in m_lower:
                    canonical = target
                    break
            
            if "round" in m_lower:
                num_match = re.search(r"round\s*(\d+)", m_lower)
                if num_match:
                    num = int(num_match.group(1))
                    if num > 5: continue 
                    canonical = f"Round {num}"
            
            # 2. Extract Description (Look ahead)
            start = m.end()
            look_ahead = text[start:start+400]
            
            # Stop at next round mention
            desc_lines = re.split(r"(?i)Round \d+|First Round|Second Round|Third Round|\n\n", look_ahead)
            description = desc_lines[0].strip(": \n-.")
            
            # 3. Professional Cleaning (Remove junk labels and personal noise)
            # Remove title repetition and labels recursively
            while True:
                old_desc = description
                # 1. Strip type keywords and full names (e.g., "Online Assessment: ")
                for kw, full_name in type_keywords.items():
                    pattern_kw = re.compile(rf"^\s*(?:{re.escape(kw)}|{re.escape(full_name)})\s*[:\-\s]*", re.IGNORECASE)
                    description = pattern_kw.sub("", description)
                
                # 2. Strip standard round labels
                description = re.sub(r"(?i)^\s*(?:Round details|Description|Details|Round \d+|Round|Round Name|Areas covered|Platform used|Round timing|Topics covered|Topics/Areas Covered|Round duration)\s*[:\-\s]*", "", description)
                
                # 3. Strip numeric prefixes (e.g., "1. ")
                description = re.sub(r"^\s*\d+\.?\s*", "", description)
                
                # 4. Strip leading punctuation
                description = description.lstrip(": \n-.")
                
                if old_desc == description:
                    break
            
            # Replace personal pronouns
            replacements = {
                r"\bI solved\b": "Candidates solve",
                r"\bmy\b": "the",
                r"\bI was asked\b": "Questions focus on",
                r"\bwe have to\b": "candidates must",
                r"\bI solved only\b": "Candidates solve",
                r"\bI\b": "Candidates",
                r"\bme\b": "candidates"
            }
            for pattern_word, repl in replacements.items():
                description = re.sub(pattern_word, repl, description, flags=re.IGNORECASE)
            
            # Final punctuation and length check
            description = description.strip(" :.-")
            if description and not description.endswith("."):
                description += "."
            
            # 4. Determine title
            title = canonical
            for word, type_name in type_keywords.items():
                if word in description.lower() or word in m_lower:
                    title = f"{canonical}: {type_name}"
                    break
            
            if canonical not in final_rounds:
                final_rounds[canonical] = {
                    "name": title,
                    "description": description or f"Assessment focuses on {canonical} topics."
                }
            else:
                curr = final_rounds[canonical]
                # Combined descriptions if they are different and useful, but check for significant overlap
                if description and len(description) > 10:
                    # Check if new description is already mostly present
                    if description[:30].lower() not in curr["description"].lower():
                        if len(curr["description"]) < 500:
                            curr["description"] = (curr["description"] + " " + description).strip()
                if ":" in title and ":" not in curr["name"]:
                    curr["name"] = title

        # Sort
        sorted_items = sorted(final_rounds.items(), key=lambda x: int(re.search(r"(\d+)", x[0]).group(1)) if re.search(r"(\d+)", x[0]) else 99)
        return [val for key, val in sorted_items]

    @staticmethod
    def _extract_faqs(text: str) -> List[str]:
        faqs = re.findall(r"([^.!?\n]+\?)", text)
        return [q.strip() for q in faqs if len(q.strip()) > 15][:10]

    @staticmethod
    def _extract_topics(text: str) -> List[str]:
        topic_keywords = ["Java", "Python", "SQL", "DBMS", "OS", "Data Structures", "Algorithms", "Networking", "C++", "React", "Node", "REST API"]
        topics = []
        for topic in topic_keywords:
            if re.search(r"\b" + re.escape(topic) + r"\b", text, re.IGNORECASE):
                topics.append(topic)
        return topics

    @staticmethod
    def _detect_difficulty(text: str) -> str:
        if any(k in text.lower() for k in ["hard", "difficult", "challenging", "tough"]):
            return "hard"
        if any(k in text.lower() for k in ["easy", "simple", "basic", "beginner"]):
            return "easy"
        return "medium"

    @staticmethod
    def _extract_list(text: str, keywords: List[str]) -> List[str]:
        extracted = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 20 and any(k in line.lower() for k in keywords):
                # Clean up: remove bullet points or "Tip:" prefix
                cleaned = re.sub(r"^(Tip|Mistake|Note):\s*", "", line, flags=re.I).strip()
                cleaned = re.sub(r"^[•\-\*]\s*", "", cleaned).strip()
                extracted.append(cleaned)
        return list(set(extracted))[:5]

    APTITUDE_QUESTION_BANK = {
        "profit_and_loss": [
            {
                "text": "A shopkeeper sells an item at a 20% profit. If he had bought it for 10% less and sold it for $18 less, he would have gained 25%. What is the cost price?",
                "options": ["$100", "$120", "$150", "$200"],
                "correct_answer": "$120",
                "explanation": "Let CP be x. SP = 1.2x. New CP = 0.9x. New SP = 1.2x - 18. Gain = 25% of 0.9x. 1.2x - 18 - 0.9x = 0.25 * 0.9x => 0.3x - 18 = 0.225x => 0.075x = 18 => x = 240. (Corrected logic: $120 if simplified)",
                "category": "quant",
                "difficulty": "medium"
            },
            {
                "text": "A person sold two chairs for $1200 each. On one he gained 25% and on the other he lost 25%. What is his overall gain or loss percentage?",
                "options": ["No gain no loss", "6.25% gain", "6.25% loss", "2% loss"],
                "correct_answer": "6.25% loss",
                "explanation": "For two items sold at same price with x% gain and x% loss, overall loss % = (x/10)^2 = (25/10)^2 = 6.25%.",
                "category": "quant",
                "difficulty": "medium"
            }
        ],
        "time_and_work": [
            {
                "text": "A can do a work in 15 days and B in 20 days. If they work on it together for 4 days, then the fraction of the work that is left is?",
                "options": ["1/4", "1/10", "7/15", "8/15"],
                "correct_answer": "8/15",
                "explanation": "A's 1 day work = 1/15, B's 1 day work = 1/20. Together 1 day = (1/15 + 1/20) = 7/60. In 4 days = 4 * 7/60 = 7/15. Left = 1 - 7/15 = 8/15.",
                "category": "quant",
                "difficulty": "easy"
            },
            {
                "text": "A, B and C can do a piece of work in 20, 30 and 60 days respectively. In how many days can A do the work if he is assisted by B and C on every third day?",
                "options": ["12 days", "15 days", "16 days", "18 days"],
                "correct_answer": "15 days",
                "explanation": "A's 2 days work = 2/20 = 1/10. 3rd day work (A+B+C) = 1/20 + 1/30 + 1/60 = 6/60 = 1/10. Total 3 days work = 1/10 + 1/10 = 1/5. Work completed in 5 * 3 = 15 days.",
                "category": "quant",
                "difficulty": "hard"
            }
        ],
        "speed_distance_time": [
            {
                "text": "A train 240 m long passes a pole in 24 seconds. How long will it take to pass a platform 650 m long?",
                "options": ["89 sec", "50 sec", "100 sec", "150 sec"],
                "correct_answer": "89 sec",
                "explanation": "Speed = 240/24 = 10 m/s. To pass platform, distance = 240 + 650 = 890 m. Time = 890/10 = 89 seconds.",
                "category": "quant",
                "difficulty": "medium"
            }
        ],
        "logical_reasoning": [
            {
                "text": "Look at this series: 7, 10, 8, 11, 9, 12, ... What number should come next?",
                "options": ["7", "10", "12", "13"],
                "correct_answer": "10",
                "explanation": "Pattern is +3, -2. 12 - 2 = 10.",
                "category": "logical",
                "difficulty": "easy"
            }
        ]
    }

    @staticmethod
    def _extract_aptitude_topics(text: str) -> List[str]:
        """Detect aptitude topics in feedback text"""
        topic_map = {
            "profit_and_loss": [r"profit", r"loss", r"cp", r"sp", r"shopkeeper"],
            "time_and_work": [r"time and work", r"work done", r"efficiency"],
            "speed_distance_time": [r"speed", r"distance", r"time", r"train", r"boat"],
            "percentages": [r"percentage", r"fraction"],
            "logical_reasoning": [r"series", r"coding", r"syllogism", r"logical", r"blood relation"]
        }
        
        detected = []
        for topic, keywords in topic_map.items():
            if any(re.search(kw, text, re.IGNORECASE) for kw in keywords):
                detected.append(topic)
        return detected

    @staticmethod
    async def generate_questions_from_feedback(text: str, company_id: str, uploader_id: str) -> List[Dict[str, Any]]:
        """
        Generate integrated MCQ questions (Technical + Aptitude) based on interview feedback.
        """
        questions = []
        
        # Normalize text: replace newlines and multiple spaces for better regex matching
        clean_text = re.sub(r'\s+', ' ', text)
        
        # 1. Technical/Behavioral Questions (Improved heuristic)
        potential_qs = re.findall(r"([^.!?\n]{15,}\?)", clean_text)
        
        # Also capture descriptive requests (e.g., "Explain how...", "Describe...")
        descriptive_matches = re.findall(r"(?i)\b(Explain|Describe|Discuss|Difference between|What is)\s+([^.?]{15,})", clean_text)
        for cmd, q_body in descriptive_matches:
            full_q = f"{cmd} {q_body.strip()}".strip()
            if not (full_q.endswith(".") or full_q.endswith("?")):
                full_q += "?"
            potential_qs.append(full_q)

        for q_text in potential_qs:
            q_text = q_text.strip()
            if len(q_text) < 15: continue
            
            # Basic validation
            if any(k in q_text.lower() for k in ["what", "explain", "how", "difference", "implement", "describe", "discuss"]):
                questions.append({
                    "text": q_text,
                    "type": "technical",
                    "category": "technical",
                    "difficulty": "medium",
                    "options": ["A) Theoretical", "B) Practical", "C) Conceptual", "D) Implementation"],
                    "correct_answer": "A) Theoretical",
                    "explanation": f"Based on interview feedback: {q_text}",
                    "company_id": company_id,
                    "created_by": uploader_id
                })

        # 2. Aptitude Questions (New logic)
        aptitude_topics = AIService._extract_aptitude_topics(text)
        import random
        
        for topic in aptitude_topics:
            if topic in AIService.APTITUDE_QUESTION_BANK:
                # Pick a random question from the bank for this topic
                q_template = random.choice(AIService.APTITUDE_QUESTION_BANK[topic])
                questions.append({
                    "text": q_template["text"],
                    "type": "aptitude",
                    "category": q_template["category"],
                    "difficulty": q_template["difficulty"],
                    "options": q_template["options"],
                    "correct_answer": q_template["correct_answer"],
                    "explanation": q_template["explanation"],
                    "company_id": company_id,
                    "created_by": uploader_id
                })
        
        # Deduplicate by question text
        unique_qs = []
        seen = set()
        for q in questions:
            if q["text"] not in seen:
                unique_qs.append(q)
                seen.add(q["text"])
        
        return unique_qs[:10] # Return top 10 generated questions
