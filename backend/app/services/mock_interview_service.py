from datetime import datetime
from typing import Any, Dict, List, Optional
import random
import re
import statistics
import logging

from fastapi import HTTPException, status

from app.models.company import Company, CompanyInsights
from app.models.mock_interview import (
    MockInterviewAnswer,
    MockInterviewFeedback,
    MockInterviewMode,
    MockInterviewQuestion,
    MockInterviewSectionScore,
    MockInterviewSession,
    MockInterviewStatus,
    MockQuestionCategory,
)
from app.services.gemini_service import GeminiEvaluator


logger = logging.getLogger(__name__)


class MockInterviewService:
    HR_QUESTION_BANK = [
        {
            "prompt": "Tell me about yourself and highlight the experiences that make you a strong fit for this role.",
            "expected_points": ["clear introduction", "relevant skills", "projects or internships", "fit for the role"],
            "topic": "self_introduction",
            "difficulty": "easy",
        },
        {
            "prompt": "Why do you want to work for this company, and what excites you about this opportunity?",
            "expected_points": ["company-specific motivation", "role alignment", "career goals", "genuine interest"],
            "topic": "motivation",
            "difficulty": "easy",
        },
        {
            "prompt": "Describe a challenging situation you faced in a project and how you handled it.",
            "expected_points": ["problem context", "actions taken", "collaboration", "result or learning"],
            "topic": "behavioral_problem_solving",
            "difficulty": "medium",
        },
        {
            "prompt": "What are your strengths, and how have you demonstrated them in academics or projects?",
            "expected_points": ["specific strength", "evidence", "impact", "self-awareness"],
            "topic": "strengths",
            "difficulty": "easy",
        },
        {
            "prompt": "Where do you see yourself professionally in the next 3 to 5 years?",
            "expected_points": ["clear direction", "skill development", "role progression", "company alignment"],
            "topic": "career_goals",
            "difficulty": "easy",
        },
        {
            "prompt": "Tell me about a time you had to work under tight deadlines. How did you manage it?",
            "expected_points": ["situation", "prioritization", "execution", "outcome"],
            "topic": "time_management",
            "difficulty": "medium",
        },
        {
            "prompt": "Describe a time you had a disagreement with a teammate. How did you resolve it?",
            "expected_points": ["conflict description", "communication", "compromise or resolution", "result"],
            "topic": "teamwork_conflict",
            "difficulty": "medium",
        },
        {
            "prompt": "What are your weaknesses, and what have you done to actively improve them?",
            "expected_points": ["honest weakness", "awareness", "improvement steps", "progress"],
            "topic": "self_improvement",
            "difficulty": "medium",
        },
        {
            "prompt": "Can you walk me through a project you are most proud of and the impact it had?",
            "expected_points": ["project description", "your role", "technical details", "measurable outcome"],
            "topic": "project_highlight",
            "difficulty": "easy",
        },
        {
            "prompt": "How do you handle feedback, especially when it is critical or unexpected?",
            "expected_points": ["open mindset", "concrete example", "implementation of feedback", "growth mindset"],
            "topic": "feedback_handling",
            "difficulty": "medium",
        },
    ]

    TECHNICAL_TOPIC_BANK = {
        "OS": [
            "Explain the difference between processes and threads, and discuss where each is preferable.",
            "What is virtual memory and why is it important in modern operating systems?",
            "How does a deadlock occur, and what are the strategies to prevent or detect it?",
        ],
        "DBMS": [
            "Explain normalization and when denormalization might still be useful.",
            "What are ACID properties and why do they matter in transactions?",
            "Compare SQL vs NoSQL databases and describe when you would choose one over the other.",
        ],
        "Networking": [
            "Compare TCP and UDP and explain suitable use cases for each.",
            "Walk through what happens when you enter a URL in the browser.",
            "What is the difference between HTTP and HTTPS, and why does it matter for security?",
        ],
        "Data Structures": [
            "How would you choose between an array, linked list, stack, queue, and hash map for a problem?",
            "Explain time complexity tradeoffs for common data structures you use in interviews.",
            "When would you use a heap versus a sorted array, and how do they differ in practice?",
        ],
        "Algorithms": [
            "How do you approach optimization after getting a brute-force solution working?",
            "Explain the difference between greedy, divide-and-conquer, and dynamic programming approaches.",
            "What is memoization and how does it differ from tabulation in dynamic programming?",
        ],
        "OOP": [
            "Explain encapsulation, inheritance, abstraction, and polymorphism with a practical example.",
            "What is composition vs inheritance, and when would you choose one over the other?",
            "What are design patterns, and can you walk through one you have used in a project?",
        ],
        "System Design": [
            "How would you design a URL shortener service, covering storage, scalability, and hashing?",
            "Explain the difference between vertical and horizontal scaling and when each is appropriate.",
            "What is a load balancer, and how does it help in building scalable backend systems?",
        ],
        "Web / APIs": [
            "What is REST, and how does it differ from GraphQL in terms of data fetching?",
            "Explain the request-response cycle in a web application from browser to database.",
            "What are HTTP status codes, and can you give examples for 200, 400, 401, 403, 404, and 500?",
        ],
        "Git / DevOps": [
            "What is the difference between git merge and git rebase, and when would you use each?",
            "What is CI/CD, and how can it improve software development quality and deployment speed?",
        ],
    }

    CODING_DISCUSSION_BANK = [
        {
            "prompt": "You solved a coding problem correctly. How would you explain your approach, time complexity, and space complexity to an interviewer?",
            "expected_points": ["problem understanding", "step-by-step approach", "time complexity", "space complexity", "tradeoffs"],
            "topic": "approach_explanation",
            "difficulty": "medium",
        },
        {
            "prompt": "Suppose your first solution works but is too slow. How would you identify bottlenecks and optimize it?",
            "expected_points": ["baseline solution", "bottleneck identification", "data structure changes", "complexity improvement"],
            "topic": "optimization",
            "difficulty": "medium",
        },
        {
            "prompt": "How do you test a coding solution before submitting it in an interview setting?",
            "expected_points": ["sample cases", "edge cases", "dry run", "failure handling"],
            "topic": "testing_strategy",
            "difficulty": "easy",
        },
        {
            "prompt": "If an interviewer gives you a tree or graph problem, how would you decide between recursion, DFS, and BFS?",
            "expected_points": ["problem structure", "traversal choice", "space-time tradeoff", "base cases"],
            "topic": "problem_strategy",
            "difficulty": "hard",
        },
        {
            "prompt": "How would you approach a sliding window problem, and what signals in the problem statement suggest it?",
            "expected_points": ["subarray or substring pattern", "two pointer technique", "window expansion and contraction", "complexity"],
            "topic": "sliding_window",
            "difficulty": "medium",
        },
        {
            "prompt": "When would you choose recursion over iteration, and what are the risks of deep recursion stacks?",
            "expected_points": ["stack overflow risk", "tail recursion", "memoization", "iterative equivalent"],
            "topic": "recursion_vs_iteration",
            "difficulty": "medium",
        },
        {
            "prompt": "Walk me through how you would implement binary search and handle off-by-one errors in the boundary conditions.",
            "expected_points": ["sorted array requirement", "mid calculation", "left and right pointer updates", "edge cases"],
            "topic": "binary_search",
            "difficulty": "easy",
        },
        {
            "prompt": "How would you explain the difference between a stack and a queue to someone unfamiliar with data structures, and give a real-world use case for each?",
            "expected_points": ["LIFO vs FIFO", "stack use case", "queue use case", "concrete example"],
            "topic": "stack_vs_queue",
            "difficulty": "easy",
        },
    ]

    @staticmethod
    async def start_session(
        user_id: str,
        mode: MockInterviewMode = MockInterviewMode.GENERAL,
        company_id: Optional[str] = None,
        question_count: int = 6,
    ) -> MockInterviewSession:
        company = None
        insights = None

        if mode == MockInterviewMode.COMPANY:
            if not company_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="company_id is required for company mock interviews")
            company = await Company.get(company_id)
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            insights = await CompanyInsights.find_one(CompanyInsights.company_id == company_id)

        questions = MockInterviewService._generate_questions(mode, company, insights, question_count)
        session = MockInterviewSession(
            user_id=user_id,
            company_id=company_id,
            company_name=company.name if company else None,
            mode=mode,
            questions=questions,
        )
        await session.insert()
        return session

    @staticmethod
    async def get_session(session_id: str, user_id: str) -> MockInterviewSession:
        session = await MockInterviewSession.get(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock interview session not found")
        return session

    @staticmethod
    async def submit_answer(session_id: str, user_id: str, answer_text: str) -> Dict[str, Any]:
        session = await MockInterviewService.get_session(session_id, user_id)

        if session.status != MockInterviewStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This mock interview session is no longer active")

        if session.current_question_index >= len(session.questions):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All questions in this session have already been answered")

        question = session.questions[session.current_question_index]
        feedback = MockInterviewService._evaluate_answer(question, answer_text)

        session.answers.append(
            MockInterviewAnswer(
                question_index=session.current_question_index,
                category=question.category,
                prompt=question.prompt,
                topic=question.topic,
                answer=answer_text,
                feedback=feedback,
            )
        )
        session.current_question_index += 1
        session.updated_at = datetime.utcnow()

        completed = session.current_question_index >= len(session.questions)
        if completed:
            await MockInterviewService._finalize_session(session)

        await session.save()

        next_question = None if completed else session.questions[session.current_question_index]
        return {
            "session": session,
            "feedback": feedback,
            "next_question": next_question,
            "completed": completed,
        }

    @staticmethod
    async def finish_session(session_id: str, user_id: str) -> MockInterviewSession:
        session = await MockInterviewService.get_session(session_id, user_id)
        if session.status == MockInterviewStatus.COMPLETED:
            return session

        await MockInterviewService._finalize_session(session)
        await session.save()
        return session

    @staticmethod
    async def get_history(user_id: str, limit: int = 10, company_id: Optional[str] = None) -> List[MockInterviewSession]:
        query = {"user_id": user_id}
        if company_id:
            query["company_id"] = company_id
        return await MockInterviewSession.find(query).sort(-MockInterviewSession.started_at).limit(limit).to_list()

    @staticmethod
    def _generate_questions(
        mode: MockInterviewMode,
        company: Optional[Company],
        insights: Optional[CompanyInsights],
        question_count: int,
    ) -> List[MockInterviewQuestion]:
        company_name = company.name if company else ""

        hr_questions = MockInterviewService._build_hr_questions(company_name, mode, company, insights)
        technical_questions = MockInterviewService._build_technical_questions(company_name, insights)
        coding_questions = MockInterviewService._build_coding_questions(company_name, insights)

        # Shuffle each bucket so repeat sessions feel different
        random.shuffle(hr_questions)
        random.shuffle(technical_questions)
        random.shuffle(coding_questions)

        # Aim for ~⅓ from each category
        per_section = max(1, question_count // 3)
        remainder = question_count - per_section * 3

        assembled = (
            hr_questions[:per_section]
            + technical_questions[:per_section]
            + coding_questions[:per_section]
        )

        # Fill remainder from whichever buckets have extras, round-robin
        extras = (
            hr_questions[per_section:]
            + technical_questions[per_section:]
            + coding_questions[per_section:]
        )
        assembled.extend(extras[:remainder])

        return assembled[:question_count]

    @staticmethod
    def _build_hr_questions(
        company_name: str,
        mode: MockInterviewMode,
        company: Optional[Company],
        insights: Optional[CompanyInsights],
    ) -> List[MockInterviewQuestion]:
        prompts = []
        for item in MockInterviewService.HR_QUESTION_BANK:
            prompt = item["prompt"]
            source = "general"
            if company_name and "company" in prompt.lower():
                prompt = prompt.replace("this company", company_name)
                source = "company_feedback"
            prompts.append(
                MockInterviewQuestion(
                    category=MockQuestionCategory.HR,
                    prompt=prompt,
                    topic=item["topic"],
                    expected_points=item["expected_points"],
                    source=source if mode == MockInterviewMode.COMPANY else "general",
                    difficulty=item["difficulty"],
                )
            )
        if company_name:
            rounds = [r.name for r in (insights.rounds_summary if insights else []) if r.name][:3]
            important_areas = list(dict.fromkeys((company.important_areas if company else [])[:4]))

            prompts.append(
                MockInterviewQuestion(
                    category=MockQuestionCategory.HR,
                    prompt=f"{company_name} usually has rounds like {', '.join(rounds) if rounds else 'online assessment, coding assessment, and technical interview'}. How would you prepare yourself and present your fit across these rounds?",
                    topic="company_readiness",
                    expected_points=["company awareness", "preparation strategy", "role fit", "confidence"],
                    source="company_feedback" if mode == MockInterviewMode.COMPANY else "general",
                    difficulty="medium",
                )
            )
            prompts.append(
                MockInterviewQuestion(
                    category=MockQuestionCategory.HR,
                    prompt=f"{company_name} often focuses on areas like {', '.join(important_areas) if important_areas else 'problem solving and core CS'}. How would you explain that your background aligns with what the company values?",
                    topic="company_alignment",
                    expected_points=["skills alignment", "project evidence", "company motivation", "clear positioning"],
                    source="company_feedback" if mode == MockInterviewMode.COMPANY else "general",
                    difficulty="medium",
                )
            )
        return prompts

    @staticmethod
    def _build_technical_questions(company_name: str, insights: Optional[CompanyInsights]) -> List[MockInterviewQuestion]:
        topics = []
        if insights and insights.insights:
            topics.extend(insights.insights.important_technical_topics or [])
        if not topics:
            topics = ["Data Structures", "Algorithms", "DBMS", "OS", "Networking", "OOP"]

        questions = []
        seen = set()
        for topic in topics:
            for prompt in MockInterviewService.TECHNICAL_TOPIC_BANK.get(topic, []):
                if prompt in seen:
                    continue
                seen.add(prompt)
                questions.append(
                    MockInterviewQuestion(
                        category=MockQuestionCategory.TECHNICAL,
                        prompt=prompt if not company_name else f"For {company_name}, {prompt[0].lower() + prompt[1:]}",
                        topic=topic,
                        expected_points=MockInterviewService._expected_points_from_prompt(prompt),
                        source="company_feedback" if insights else "general",
                        difficulty="medium",
                    )
                )

        if insights and insights.insights and insights.insights.technical_questions:
            for item in insights.insights.technical_questions[:3]:
                if item.question in seen:
                    continue
                seen.add(item.question)
                questions.append(
                    MockInterviewQuestion(
                        category=MockQuestionCategory.TECHNICAL,
                        prompt=item.question,
                        topic=item.topic,
                        expected_points=["concept explanation", "example", "tradeoffs", "practical relevance"],
                        source="company_feedback",
                        difficulty="medium",
                    )
                )

        if company_name and topics:
            for topic in topics[:3]:
                prompt = f"For {company_name}, explain one interview-ready answer on {topic} that is concise, technically correct, and backed by an example."
                if prompt in seen:
                    continue
                seen.add(prompt)
                questions.append(
                    MockInterviewQuestion(
                        category=MockQuestionCategory.TECHNICAL,
                        prompt=prompt,
                        topic=topic,
                        expected_points=["clear concept explanation", "example", "interview-ready structure", "practical relevance"],
                        source="company_feedback",
                        difficulty="medium",
                    )
                )

        return questions

    @staticmethod
    def _build_coding_questions(company_name: str, insights: Optional[CompanyInsights]) -> List[MockInterviewQuestion]:
        questions = []
        coding_difficulty = insights.insights.coding_difficulty if insights and insights.insights else "medium"
        technical_topics = insights.insights.important_technical_topics if insights and insights.insights else []

        for item in MockInterviewService.CODING_DISCUSSION_BANK:
            prompt = item["prompt"]
            if company_name:
                prompt = f"In a {company_name} interview, {prompt[0].lower() + prompt[1:]}"

            questions.append(
                MockInterviewQuestion(
                    category=MockQuestionCategory.CODING,
                    prompt=prompt,
                    topic=item["topic"],
                    expected_points=item["expected_points"] + ([coding_difficulty] if coding_difficulty else []),
                    source="company_feedback" if insights else "general",
                    difficulty=coding_difficulty or item["difficulty"],
                )
            )

        if technical_topics:
            questions.append(
                MockInterviewQuestion(
                    category=MockQuestionCategory.CODING,
                    prompt=f"Pick one likely {company_name or 'interview'} topic from {', '.join(technical_topics[:3])} and explain how you would derive an efficient coding solution under interview pressure.",
                    topic="company_problem_solving",
                    expected_points=["problem breakdown", "data structure choice", "optimization", "edge cases"],
                    source="company_feedback",
                    difficulty=coding_difficulty or "medium",
                )
            )

        if company_name:
            questions.append(
                MockInterviewQuestion(
                    category=MockQuestionCategory.CODING,
                    prompt=f"In a {company_name} coding interview, how would you explain edge cases, testing strategy, and optimization tradeoffs after writing a working solution?",
                    topic="company_coding_review",
                    expected_points=["edge cases", "testing strategy", "optimization tradeoffs", "communication clarity"],
                    source="company_feedback",
                    difficulty=coding_difficulty or "medium",
                )
            )

        return questions

    @staticmethod
    def _expected_points_from_prompt(prompt: str) -> List[str]:
        lowered = prompt.lower()
        points = ["clear explanation", "relevant example"]
        if "difference" in lowered or "compare" in lowered:
            points.append("comparison")
        if "time complexity" in lowered or "complexity" in lowered:
            points.append("complexity analysis")
        if "why" in lowered:
            points.append("reasoning")
        if "design" in lowered or "scalab" in lowered:
            points.append("system design thinking")
        if "test" in lowered or "edge case" in lowered:
            points.append("edge case handling")
        return list(dict.fromkeys(points))

    @staticmethod
    def _evaluate_answer(question: MockInterviewQuestion, answer_text: str) -> MockInterviewFeedback:
        cleaned = re.sub(r"\s+", " ", answer_text).strip()
        words = re.findall(r"\b\w+\b", cleaned.lower())
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r"[.!?]+", cleaned) if s.strip()]

        # --- Semantic AI-based Evaluation (Gemini/ML) ---
        ai_result = GeminiEvaluator.evaluate_semantic_fit(
            question.prompt, 
            answer_text, 
            question.expected_points or []
        )
        
        relevance = ai_result["score"]
        technical_accuracy = ai_result["coverage"]

        # --- Rule-based Heuristics for Presence & Style ---
        # Clarity: Word count + fillers + sentence variety
        filler_words = ["um", "uh", "actually", "basically", "you know", "like"]
        filler_count = sum(1 for w in filler_words if f" {w} " in f" {cleaned.lower()} ")
        clarity = min(100.0, 40.0 + min(word_count, 150) * 0.4)
        clarity = max(clarity - (filler_count * 8), 30.0)

        # Structure: detects organized answer signals
        structure_terms = ["first", "second", "finally", "approach", "example", "result", "initially"]
        structure_hits = sum(1 for term in structure_terms if term in cleaned.lower())
        structure = min(100.0, 30.0 + structure_hits * 12.0 + len(sentences) * 6.0)

        # Confidence: assertive language
        assertive_phrases = ["i delivered", "i improved", "i learned", "i built", "i solved", "i led"]
        conf_hits = sum(1 for p in assertive_phrases if p in cleaned.lower())
        confidence = min(100.0, 40.0 + conf_hits * 15.0 + (word_count // 50) * 10)
        if word_count < 25: confidence = max(confidence - 20, 10.0)

        # --- Composite score ---
        score = round(
            relevance * 0.35 +
            clarity * 0.15 +
            structure * 0.15 +
            technical_accuracy * 0.25 +
            confidence * 0.10,
            2
        )

        strengths = ai_result["strengths"]
        improvements = ai_result["improvements"]

        if clarity >= 75: strengths.append("Your explanation is clear and easy to follow.")
        if structure < 60: improvements.append("Try using transition words like 'firstly' or 'moreover' to improve flow.")
        if word_count < 40: improvements.append("Provide more detailed examples to increase the depth of your answer.")

        suggested_answer = f"Goal: {question.prompt}. Key points: " + ", ".join(question.expected_points or ["general context"])

        return MockInterviewFeedback(
            relevance=round(relevance, 2),
            clarity=round(clarity, 2),
            structure=round(structure, 2),
            technical_accuracy=round(technical_accuracy, 2),
            confidence=round(confidence, 2),
            score=score,
            strengths=strengths[:3],
            improvements=improvements[:3],
            suggested_answer=suggested_answer,
        )


    @staticmethod
    async def _finalize_session(session: MockInterviewSession) -> None:
        try:
            section_map = {
                MockQuestionCategory.HR.value: [],
                MockQuestionCategory.TECHNICAL.value: [],
                MockQuestionCategory.CODING.value: [],
            }
            for answer in session.answers:
                if answer.category and answer.category.value in section_map:
                    section_map[answer.category.value].append(answer.feedback.score)

            session.section_scores = MockInterviewSectionScore(
                hr=round(statistics.mean(section_map["hr"]), 2) if section_map["hr"] else 0.0,
                technical=round(statistics.mean(section_map["technical"]), 2) if section_map["technical"] else 0.0,
                coding=round(statistics.mean(section_map["coding"]), 2) if section_map["coding"] else 0.0,
            )

            weighted_parts = []
            total_weight = 0.0
            if section_map["hr"]:
                weighted_parts.append(session.section_scores.hr * 0.25)
                total_weight += 0.25
            if section_map["technical"]:
                weighted_parts.append(session.section_scores.technical * 0.35)
                total_weight += 0.35
            if section_map["coding"]:
                weighted_parts.append(session.section_scores.coding * 0.40)
                total_weight += 0.40

            session.overall_score = round(sum(weighted_parts) / total_weight, 2) if total_weight else 0.0

            session.summary = MockInterviewService._build_summary(session)
            session.recommendations = MockInterviewService._build_recommendations(session)
            
            try:
                comparison = await MockInterviewService._build_comparison(session)
                session.comparison_summary = comparison["summary"]
                session.improved_areas = comparison["improved_areas"]
                session.focus_areas = comparison["focus_areas"]
            except Exception as ce:
                logger.error(f"Error building comparison for session {session.id}: {ce}")
                session.comparison_summary = "Progress insights are temporarily unavailable."

            session.status = MockInterviewStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to finalize mock interview session {session.id}: {e}")
            # Fallback to avoid complete failure
            session.status = MockInterviewStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            if not session.summary:
                session.summary = "Session completed. Review your individual answers below."

    @staticmethod
    def _build_summary(session: MockInterviewSession) -> str:
        score = session.overall_score
        answered = len(session.answers)
        total = len(session.questions)
        if answered < total:
            return f"Session ended early with {answered} of {total} questions answered. Review your completed answers below."
        if score >= 80:
            return "Excellent mock interview performance! Your answers are well-structured, relevant, and interview-ready."
        if score >= 65:
            return "Strong mock interview performance. Your answers show good structure and relevance with room for further depth."
        if score >= 50:
            return "Moderate mock interview performance. You have good foundations but still need more depth and polish."
        return "Early-stage mock interview performance. Focus on structure, relevance, and clearer technical communication."

    @staticmethod
    def _build_recommendations(session: MockInterviewSession) -> List[str]:
        recommendations = []
        if session.section_scores.hr < 60:
            recommendations.append("Practice concise HR answers using a STAR-style structure with clear outcomes.")
        if session.section_scores.technical < 60:
            recommendations.append("Revise core concepts and explain them aloud with examples, tradeoffs, and real use cases.")
        if session.section_scores.coding < 60:
            recommendations.append("Improve coding discussions by clearly explaining approach, complexity, and edge-case testing.")
        if session.section_scores.hr >= 60 and session.section_scores.technical >= 60 and session.section_scores.coding >= 60:
            recommendations.append("Good performance across all sections. Keep practicing with company-specific sessions to stay sharp.")
        if session.overall_score >= 75:
            recommendations.append("Consider attempting company mock interviews to benchmark yourself against company-specific expectations.")
        if len(session.answers) < len(session.questions):
            recommendations.append("Complete the full set of questions next time — finishing all rounds gives a more accurate picture of your readiness.")
        return recommendations[:4]

    @staticmethod
    async def _build_comparison(session: MockInterviewSession) -> Dict[str, Any]:
        query = {
            "user_id": session.user_id,
            "status": MockInterviewStatus.COMPLETED,
        }
        if session.company_id:
            query["company_id"] = session.company_id
        else:
            query["mode"] = MockInterviewMode.GENERAL

        previous_sessions = await MockInterviewSession.find(query).sort(-MockInterviewSession.completed_at).limit(5).to_list()
        previous_sessions = [item for item in previous_sessions if str(item.id) != str(session.id)]

        if not previous_sessions:
            prefix = f"For {session.company_name}, " if session.company_name else ""
            return {
                "summary": prefix + "complete one more mock interview to unlock attempt-vs-attempt comparison.",
                "improved_areas": ["This is your baseline mock interview for this context."],
                "focus_areas": ["Retake the mock interview after practicing your weaker sections to see measurable improvement."],
            }

        previous = previous_sessions[0]
        improved_areas = []
        focus_areas = []

        score_delta = round(session.overall_score - previous.overall_score, 2)
        if score_delta >= 3:
            improved_areas.append(f"Overall mock interview score improved by {score_delta:.0f}% compared with your previous {'company' if session.company_id else 'general'} session.")
        elif score_delta <= -3:
            focus_areas.append(f"Overall score dropped by {abs(score_delta):.0f}% from the previous session, so review your weaker answers before the next attempt.")

        section_labels = {
            "hr": "HR communication",
            "technical": "technical explanation",
            "coding": "coding discussion",
        }
        current_scores = {
            "hr": session.section_scores.hr,
            "technical": session.section_scores.technical,
            "coding": session.section_scores.coding,
        }
        previous_scores = {
            "hr": previous.section_scores.hr,
            "technical": previous.section_scores.technical,
            "coding": previous.section_scores.coding,
        }

        for key, label in section_labels.items():
            delta = round(current_scores[key] - previous_scores[key], 2)
            if delta >= 4:
                improved_areas.append(f"Your {label} improved by {delta:.0f}% compared with the last session.")
            elif delta <= -4:
                focus_areas.append(f"Your {label} dropped by {abs(delta):.0f}%, so practice this area again.")
            elif current_scores[key] > 0 and current_scores[key] < 55:
                focus_areas.append(f"Your {label} is still below 55%, so it remains a priority improvement area.")

        if session.company_name:
            summary = (
                f"For {session.company_name}, this report compares your latest mock interview against your previous company-specific attempt. "
                f"Use it to understand which interview sections are improving and which still need revision."
            )
        else:
            summary = "This report compares your latest mock interview against your previous general attempt."

        if not improved_areas:
            improved_areas.append("No major jump is visible yet, but repeated practice will make your progress trend clearer.")
        if not focus_areas:
            focus_areas.append("No major regression is visible right now. Keep practicing to build consistency across all interview sections.")

        return {
            "summary": summary,
            "improved_areas": improved_areas[:3],
            "focus_areas": focus_areas[:3],
        }
