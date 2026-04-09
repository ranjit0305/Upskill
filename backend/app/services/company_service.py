from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.models.performance import Performance, ReadinessScore
from app.models.assessment import Submission, Assessment, QuestionType
from typing import List, Dict, Any
from datetime import datetime
import re
import statistics

class CompanyService:
    @staticmethod
    async def get_company_prep_dashboard(user_id: str, company_id: str) -> Dict[str, Any]:
        """Combine company insights and user performance for the dashboard"""
        from beanie import PydanticObjectId
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Handle both string and ObjectId lookups
            lookup_id = None
            if isinstance(company_id, str) and len(company_id) == 24:
                try:
                    lookup_id = PydanticObjectId(company_id)
                except:
                    pass
            
            if lookup_id:
                company = await Company.get(lookup_id)
            else:
                company = await Company.find_one(Company.id == company_id)
                
            if not company:
                logger.warning(f"Company not found in DB: {company_id}")
                return None
                
            insights = await CompanyInsights.find_one(CompanyInsights.company_id == str(company.id))
            CompanyService._sanitize_dashboard_data(company, insights)

            # rounds_summary is populated ONLY from uploaded feedback — no defaults injected here

            # Calculate company-specific readiness
            assessment_summary = await CompanyService.get_company_assessment_summary(user_id, str(company.id))
            readiness = assessment_summary["overall_score"]

            # Generate personalized recommendations
            learning_path = await CompanyService.generate_learning_path(user_id, str(company.id), insights)

            # Fetch questions generated based on this company's feedback
            from app.models.assessment import Question
            generated_questions = await Question.find({
                "companies": str(company.id),
                "tags": {"$in": ["source:feedback", "source:web"]}
            }).sort(-Question.created_at).limit(10).to_list()
            feedback_count = await InterviewFeedback.find(InterviewFeedback.company_id == str(company.id)).count()

            return {
                "company": company,
                "insights": insights,
                "readiness_score": readiness,
                "assessment_summary": assessment_summary,
                "learning_path": learning_path,
                "generated_questions": generated_questions,
                "company_profile": CompanyService.build_dashboard_profile(company, insights, feedback_count)
            }
        except Exception as e:
            logger.error(f"Error in get_company_prep_dashboard for {company_id}: {str(e)}", exc_info=True)
            # Re-raise so it becomes a 500 error instead of a mysterious 404
            raise

    @staticmethod
    async def update_company_from_feedback(company_id: str, raw_insights: Dict[str, Any], extracted_text: str):
        """Persist extracted company-facing details after feedback ingestion."""
        company = await Company.get(company_id)
        if not company:
            return None

        round_names = [
            r.get("name", "").strip()
            for r in raw_insights.get("rounds", [])
            if r.get("name", "").strip()
        ]
        topics = [
            topic.strip()
            for topic in raw_insights.get("topics", [])
            if isinstance(topic, str) and topic.strip()
        ]

        merged_rounds = CompanyService._merge_unique(company.interview_rounds, round_names, limit=8)
        merged_topics = CompanyService._merge_unique(company.important_areas, topics, limit=10)

        company.interview_rounds = merged_rounds
        company.important_areas = merged_topics

        generated_description = CompanyService._build_company_description(
            company.name,
            raw_insights,
            extracted_text,
            company.description
        )
        if generated_description:
            company.description = generated_description

        await company.save()
        return company

    @staticmethod
    def build_dashboard_profile(company: Company, insights: CompanyInsights, feedback_count: int) -> Dict[str, Any]:
        """Build a compact company profile for the dashboard."""
        rounds = insights.rounds_summary if insights else []
        insight_meta = insights.insights if insights else None

        return {
            "summary": company.description,
            "focus_areas": company.important_areas,
            "interview_rounds": company.interview_rounds,
            "coding_difficulty": insight_meta.coding_difficulty if insight_meta else "unknown",
            "feedback_count": feedback_count,
            "rounds_count": len(rounds),
            "last_updated": insights.last_updated.isoformat() if insights else None
        }

    @staticmethod
    def _merge_unique(existing: List[str], incoming: List[str], limit: int) -> List[str]:
        merged = []
        seen = set()

        for value in (existing or []) + (incoming or []):
            cleaned = re.sub(r"\s+", " ", str(value).strip())
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
            if len(merged) >= limit:
                break

        return merged

    @staticmethod
    def _build_company_description(
        company_name: str,
        raw_insights: Dict[str, Any],
        extracted_text: str,
        current_description: str
    ) -> str:
        """Generate a concise dashboard summary from uploaded feedback."""
        rounds = [
            r.get("name", "").strip()
            for r in raw_insights.get("rounds", [])
            if r.get("name", "").strip()
        ]
        topics = [
            topic.strip()
            for topic in raw_insights.get("topics", [])
            if isinstance(topic, str) and topic.strip()
        ]
        difficulty = raw_insights.get("difficulty", "medium")

        text_summary = CompanyService._extract_summary_sentences(extracted_text)
        if text_summary:
            return text_summary

        parts = []
        if rounds:
            preview_rounds = ", ".join(rounds[:3])
            suffix = " and more" if len(rounds) > 3 else ""
            parts.append(f"{company_name} commonly includes {preview_rounds}{suffix}.")
        if topics:
            preview_topics = ", ".join(topics[:4])
            parts.append(f"Key focus areas include {preview_topics}.")
        if difficulty:
            parts.append(f"Coding difficulty currently trends {difficulty}.")

        if parts:
            return " ".join(parts)

        return current_description

    @staticmethod
    def _extract_summary_sentences(extracted_text: str) -> str:
        """Pick a short human-readable summary from the uploaded feedback text."""
        if not extracted_text:
            return ""

        cleaned = re.sub(r"\s+", " ", extracted_text).strip()
        if not cleaned:
            return ""

        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        useful = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 45 or len(sentence) > 220:
                continue

            lower = sentence.lower()
            if any(term in lower for term in ["company", "round", "interview", "asked", "technical", "coding", "assessment"]):
                useful.append(sentence)
            if len(useful) == 2:
                break

        return " ".join(useful)

    @staticmethod
    def _sanitize_dashboard_data(company: Company, insights: CompanyInsights) -> None:
        """Clean noisy extracted content before returning dashboard data."""
        company.interview_rounds = CompanyService._merge_unique(
            [],
            [CompanyService._clean_label(value) for value in company.interview_rounds],
            limit=8,
        )
        company.important_areas = CompanyService._merge_unique(
            [],
            [CompanyService._clean_label(value) for value in company.important_areas],
            limit=10,
        )

        if insights:
            cleaned_rounds = []
            for round_item in insights.rounds_summary or []:
                clean_name = CompanyService._clean_label(round_item.name) or "Interview Round"
                clean_description = CompanyService._clean_round_description(round_item.description, clean_name)
                if not clean_description:
                    continue
                round_item.name = clean_name
                round_item.description = clean_description
                cleaned_rounds.append(round_item)
            insights.rounds_summary = cleaned_rounds

            if insights.insights:
                insights.insights.frequently_asked_questions = CompanyService._clean_question_list(
                    insights.insights.frequently_asked_questions
                )
                insights.insights.common_mistakes = CompanyService._clean_bullet_list(
                    insights.insights.common_mistakes
                )
                insights.insights.preparation_tips = CompanyService._clean_bullet_list(
                    insights.insights.preparation_tips
                )

        company.description = CompanyService._build_display_summary(company, insights)

    @staticmethod
    def _build_display_summary(company: Company, insights: CompanyInsights) -> str:
        existing = CompanyService._clean_summary(company.description)
        if existing and len(existing.split()) >= 8:
            return existing

        rounds = [item.name for item in (insights.rounds_summary if insights else []) if item.name]
        topics = company.important_areas or []
        coding_difficulty = insights.insights.coding_difficulty if insights and insights.insights else None

        parts = []
        if rounds:
            parts.append(f"{company.name} usually includes {', '.join(rounds[:3])}.")
        if topics:
            parts.append(f"Common focus areas are {', '.join(topics[:4])}.")
        if coding_difficulty:
            parts.append(f"Coding difficulty is typically {coding_difficulty}.")

        return " ".join(parts) if parts else (company.description or "")

    @staticmethod
    def _clean_summary(text: str) -> str:
        cleaned = CompanyService._normalize_text(text)
        if CompanyService._looks_noisy(cleaned):
            return ""
        return cleaned[:220].rstrip(" ,;:")

    @staticmethod
    def _clean_round_description(text: str, round_name: str) -> str:
        cleaned = CompanyService._normalize_text(text)
        if not cleaned:
            return ""

        noise_patterns = [
            r"(?i)\bquestion\s+question\b.*",
            r"(?i)\bdid you\b.*",
            r"(?i)\byour comments?\b.*",
            r"(?i)\breferences?\b.*",
            r"(?i)\bdetails?\b\s*[:=-]?",
            r"(?i)\bhow did you\b.*",
            r"(?i)\bi\s*\(\d+\s*minutes?\)",
            r"(?i)\bplatform\b.*",
        ]
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, "", cleaned).strip()

        cleaned = re.sub(rf"(?i)^{re.escape(round_name)}\s*[:,-]?\s*", "", cleaned).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -,:;.")
        cleaned = re.split(r"(?<=[.!?])\s+", cleaned)[:2]
        cleaned = " ".join(cleaned).strip()
        cleaned = re.sub(r"\bwas c\.$", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = cleaned.rstrip(".")

        if CompanyService._looks_noisy(cleaned):
            return CompanyService._fallback_round_summary(round_name)

        cleaned = cleaned[:220].rstrip(" ,;:")
        if not cleaned:
            return CompanyService._fallback_round_summary(round_name)
        if not cleaned.endswith("."):
            cleaned += "."
        return cleaned[0].upper() + cleaned[1:]

    @staticmethod
    def _clean_question_list(items: List[str]) -> List[str]:
        cleaned_items = []
        seen = set()
        for item in items or []:
            cleaned = CompanyService._normalize_text(item)
            cleaned = re.sub(r"(?i)^(question|faq)\s*[:.-]?\s*", "", cleaned).strip()
            normalized_alpha = re.sub(r"[^a-z]", "", cleaned.lower())
            if (
                len(cleaned) < 10
                or len(cleaned) > 180
                or not cleaned.endswith("?")
                or cleaned.isupper()
                or len(normalized_alpha) < 8
                or CompanyService._looks_noisy(cleaned)
            ):
                continue
            if not re.search(r"[a-z]{3,}\s+[a-z]{3,}", cleaned.lower()):
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned_items.append(cleaned[0].upper() + cleaned[1:])
        return cleaned_items[:5]

    @staticmethod
    def _clean_bullet_list(items: List[str]) -> List[str]:
        cleaned_items = []
        seen = set()
        for item in items or []:
            cleaned = CompanyService._normalize_text(item)
            cleaned = re.sub(r"(?i)^(tip|mistake|note|advice)\s*[:.-]?\s*", "", cleaned).strip()
            normalized_alpha = re.sub(r"[^a-z]", "", cleaned.lower())
            if (
                len(cleaned) < 12
                or len(cleaned) > 180
                or cleaned.isupper()
                or len(normalized_alpha) < 12
                or CompanyService._looks_noisy(cleaned)
            ):
                continue
            if not re.search(r"[a-z]{3,}\s+[a-z]{3,}", cleaned.lower()):
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned_items.append(cleaned[0].upper() + cleaned[1:])
        return cleaned_items[:4]

    @staticmethod
    def _clean_label(value: str) -> str:
        cleaned = CompanyService._normalize_text(value)
        return cleaned[:60].strip(" -,:;")

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        cleaned = str(text).replace("â€¢", " ").replace("â€“", "-").replace("â€”", "-")
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _looks_noisy(text: str) -> bool:
        if not text:
            return True
        lowered = text.lower()
        noise_terms = [
            "question question",
            "your comments",
            "how did you",
            "references",
            "sites / books",
            "details about questions",
            "prepared by",
            "submitted by",
            "intern offered",
            "have you placed",
            "and off on multiples",
            "suggest for preparation",
            "sites / books you suggest",
            "books you suggest",
            "general tips",
            "cleared the round",
        ]
        return any(term in lowered for term in noise_terms)

    @staticmethod
    def _fallback_round_summary(round_name: str) -> str:
        defaults = {
            "Online Assessment": "Typically starts with aptitude, logical reasoning, and technical screening questions.",
            "Coding Assessment": "Usually includes timed coding problems with an emphasis on correctness and edge cases.",
            "Technical Interview": "Focuses on core CS concepts, problem solving, and project discussions.",
            "HR Interview": "Covers communication, motivation, and culture-fit questions.",
        }
        return defaults.get(round_name, "Interview round details were extracted from uploaded feedback.")

    @staticmethod
    async def calculate_readiness(user_id: str, company_id: str) -> float:
        """
        Calculate a company-specific readiness score (0–100).
        Logic: Weight user's performance in categories important to the company.
        """
        # Fetch overall performance
        performances = await Performance.find(Performance.user_id == user_id).to_list()
        perf_map = {p.category: p.metrics.accuracy for p in performances}
        
        # Default weights (could be dynamic based on insights in future)
        weights = {
            "aptitude": 0.3,
            "technical": 0.3,
            "coding": 0.4
        }
        
        score = 0.0
        total_weight = 0.0
        
        for category, weight in weights.items():
            if category in perf_map:
                score += perf_map[category] * weight
            total_weight += weight
            
        final_score = (score / total_weight) * 100 if total_weight > 0 else 0
        return round(final_score, 2)

    @staticmethod
    async def calculate_company_assessment_readiness(user_id: str, company_id: str) -> float:
        """
        Calculate company readiness from cumulative aptitude, technical, and coding
        assessment submissions generated for this company.
        """
        summary = await CompanyService.get_company_assessment_summary(user_id, company_id)
        return summary["overall_score"]

    @staticmethod
    async def get_company_assessment_summary(user_id: str, company_id: str) -> Dict[str, Any]:
        """
        Return cumulative company assessment summary including score breakdown
        and comparison against previous attempts.
        """
        company_assessments = await Assessment.find({
            "is_generated": True,
            "description": {"$regex": company_id},
            "type": {"$in": [QuestionType.APTITUDE, QuestionType.TECHNICAL, QuestionType.CODING]},
        }).to_list()

        if not company_assessments:
            return CompanyService._empty_assessment_summary()

        assessment_type_map = {
            str(assessment.id): (
                assessment.type.value if hasattr(assessment.type, "value") else str(assessment.type).lower()
            )
            for assessment in company_assessments
        }
        submissions = await Submission.find({
            "user_id": user_id,
            "assessment_id": {"$in": list(assessment_type_map.keys())},
        }).sort(Submission.submitted_at).to_list()

        if not submissions:
            return CompanyService._empty_assessment_summary()

        component_scores = {
            "aptitude": [],
            "technical": [],
            "coding": [],
        }

        for submission in submissions:
            assessment_type = assessment_type_map.get(submission.assessment_id)
            if assessment_type not in component_scores:
                continue

            score_value = submission.total_score if submission.total_score > 0 else submission.accuracy
            component_scores[assessment_type].append({
                "score": score_value,
                "submitted_at": submission.submitted_at,
                "assessment_id": submission.assessment_id,
            })

        weights = {
            "aptitude": 0.3,
            "technical": 0.3,
            "coding": 0.4,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for category, weight in weights.items():
            if not component_scores[category]:
                continue
            avg_score = statistics.mean([item["score"] for item in component_scores[category]])
            weighted_score += avg_score * weight
            total_weight += weight

        if total_weight == 0:
            return CompanyService._empty_assessment_summary()

        overall_score = round(weighted_score / total_weight, 2)
        breakdown = {}

        for category in ["aptitude", "technical", "coding"]:
            attempts = component_scores[category]
            if attempts:
                latest_score = attempts[-1]["score"]
                previous_score = attempts[-2]["score"] if len(attempts) > 1 else None
                average_score = round(statistics.mean([item["score"] for item in attempts]), 2)
                delta = round(latest_score - previous_score, 2) if previous_score is not None else None
            else:
                latest_score = 0.0
                previous_score = None
                average_score = 0.0
                delta = None

            breakdown[category] = {
                "latest_score": round(latest_score, 2),
                "average_score": average_score,
                "previous_score": round(previous_score, 2) if previous_score is not None else None,
                "delta": delta,
                "attempts": len(attempts),
            }

        progress = CompanyService._build_progress_comparison(breakdown, overall_score)

        return {
            "overall_score": overall_score,
            "breakdown": breakdown,
            "progress": progress,
        }

    @staticmethod
    def _empty_assessment_summary() -> Dict[str, Any]:
        return {
            "overall_score": 0.0,
            "breakdown": {
                "aptitude": {"latest_score": 0.0, "average_score": 0.0, "previous_score": None, "delta": None, "attempts": 0},
                "technical": {"latest_score": 0.0, "average_score": 0.0, "previous_score": None, "delta": None, "attempts": 0},
                "coding": {"latest_score": 0.0, "average_score": 0.0, "previous_score": None, "delta": None, "attempts": 0},
            },
            "progress": {
                "summary": "Complete the company aptitude, technical, and coding tests to unlock your cumulative readiness insights.",
                "improved_areas": [],
                "focus_areas": [],
            },
        }

    @staticmethod
    def _build_progress_comparison(breakdown: Dict[str, Dict[str, Any]], overall_score: float) -> Dict[str, Any]:
        labels = {
            "aptitude": "Aptitude",
            "technical": "Technical",
            "coding": "Coding",
        }
        improved_areas = []
        focus_areas = []

        for category, data in breakdown.items():
            label = labels[category]
            delta = data["delta"]
            avg_score = data["average_score"]
            attempts = data["attempts"]

            if delta is not None and delta >= 3:
                improved_areas.append(f"{label} improved by {delta:.0f}% compared with your previous attempt.")
            elif attempts >= 2 and delta is not None and delta <= -3:
                focus_areas.append(f"{label} dropped by {abs(delta):.0f}% from the previous attempt, so revise this section again.")

            if avg_score < 40 and attempts > 0:
                focus_areas.append(f"{label} average is only {avg_score:.0f}%, so this is a priority improvement area.")
            elif avg_score >= 70:
                improved_areas.append(f"{label} is a strength right now with an average score of {avg_score:.0f}%.")

        if not improved_areas:
            improved_areas.append("You have started building your company-specific assessment history. Keep completing sections to surface clear improvement trends.")

        if not focus_areas:
            focus_areas.append("No major weak section is visible yet. Continue practicing consistently to improve your overall readiness.")

        if overall_score >= 70:
            summary = "Your cumulative performance is strong. Focus on maintaining consistency across all three sections."
        elif overall_score >= 40:
            summary = "You are making progress, but one or more sections still need improvement to raise your overall readiness."
        else:
            summary = "Your cumulative score is still early-stage. Prioritize weaker sections and retake tests to track improvement."

        return {
            "summary": summary,
            "improved_areas": improved_areas[:3],
            "focus_areas": focus_areas[:3],
        }

    @staticmethod
    async def generate_learning_path(user_id: str, company_id: str, insights: CompanyInsights) -> List[Dict[str, Any]]:
        """Prioritize topics based on frequency in feedback and user weakness"""
        if not insights:
            return []
            
        performance = await Performance.find_one(Performance.user_id == user_id, Performance.category == "overall")
        weak_topics = performance.weak_topics if performance else []
        
        learning_path = []
        
        # High priority: Topics important to company and weak for user
        company_topics = insights.insights.important_technical_topics
        
        for topic in company_topics:
            priority = "high" if topic in weak_topics else "medium"
            learning_path.append({
                "topic": topic,
                "priority": priority,
                "reason": "Frequently asked in this company's interviews" if priority == "medium" else "Critical topic and needs improvement"
            })
            
        return learning_path
