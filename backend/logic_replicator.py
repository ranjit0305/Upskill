import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.assessment import Question, Assessment, Submission, QuestionType, DifficultyLevel
from app.models.user import User
from app.models.company import Company, CompanyInsights, InterviewFeedback
from app.config import settings

async def replicate_logic():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Question, Assessment, Submission, Company, CompanyInsights, InterviewFeedback]
    )

    company_id = "6999ddda05dccabeb542db93"
    user_id = "test_user_id"
    company_name = company_id.lower()

    print("Step 1: Get coding topics")
    coding_topics = ["arrays", "strings", "linked_list"]
    print(f"Topics: {coding_topics}")

    print("Step 2: Collect Coding Questions")
    search_terms = list(set([company_id, company_name]))
    
    existing_company_qs = await Question.find({
        "companies": {"$in": search_terms},
        "type": QuestionType.CODING
    }).to_list()
    print(f"Existing company questions: {len(existing_company_qs)}")
    
    final_qs = existing_company_qs
    
    if len(final_qs) < 5:
        print("Priority 2: Topic-based questions")
        topic_qs = await Question.find({
            "category": {"$in": coding_topics},
            "type": QuestionType.CODING,
            "_id": {"$nin": [q.id for q in final_qs]}
        }).limit(5 - len(final_qs)).to_list()
        final_qs.extend(topic_qs)
        print(f"After Priority 2, total: {len(final_qs)}")

    if len(final_qs) < 5:
        print("Priority 3: Fallback from AIService Bank")
        from app.services.ai_service import AIService
        print(f"Bank keys available: {list(AIService.CODING_QUESTION_BANK.keys())}")
        for topic in coding_topics:
            if len(final_qs) >= 5: break
            bank = AIService.CODING_QUESTION_BANK.get(topic, [])
            print(f"  Topic: {topic}, Bank size: {len(bank)}")
            for q_temp in bank:
                if len(final_qs) >= 5: break
                print(f"    Creating: {q_temp['title']}")
                new_q = Question(
                    type=QuestionType.CODING,
                    category=topic,
                    difficulty=q_temp["difficulty"],
                    question=q_temp["description"],
                    test_cases=q_temp["test_cases"],
                    companies=[company_id, company_name],
                    is_generated=True,
                    created_by=user_id,
                    correct_answer="Check test cases",
                    explanation=f"Problem: {q_temp['title']}"
                )
                await new_q.insert()
                final_qs.append(new_q)
                print(f"    Inserted and added. Current total: {len(final_qs)}")

    if not final_qs:
        print("ERROR: final_qs is empty!")
    else:
        print(f"SUCCESS: Generated {len(final_qs)} questions.")
        print(f"DEBUG: questions list: {[str(q.id) for q in final_qs[:5]]}")
        
        try:
            assessment = Assessment(
                title=f"Coding Assessment",
                description=f"A specialized coding test for {company_id} based on recent patterns.",
                type=QuestionType.CODING,
                questions=[str(q.id) for q in final_qs[:5]],
                duration=90,
                total_marks=len(final_qs[:5]),
                difficulty_level=DifficultyLevel.MEDIUM,
                is_generated=True,
                created_by=user_id
            )
            print("DEBUG: Inserting assessment...")
            await assessment.insert()
            print(f"DEBUG: Assessment inserted with ID: {assessment.id}")
        except Exception as e:
            print(f"EXCEPTION during Assessment creation: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(replicate_logic())
