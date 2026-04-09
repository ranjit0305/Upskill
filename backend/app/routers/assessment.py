from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from app.schemas.assessment import (
    QuestionCreate, QuestionResponse, QuestionDetail,
    AssessmentCreate, AssessmentResponse,
    SubmissionCreate, SubmissionResponse, SubmissionDetail
)
from app.services.assessment_service import AssessmentService
from app.services.auth_service import AuthService
from app.models.user import UserRole

router = APIRouter(prefix="/assessment", tags=["Assessment"])
security = HTTPBearer()


async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user"""
    return await AuthService.get_current_user(credentials.credentials)


@router.post("/questions", response_model=QuestionDetail, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    current_user = Depends(get_current_user_from_token)
):
    """Create a new question (Admin/Senior only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SENIOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and seniors can create questions"
        )
    
    question = await AssessmentService.create_question(question_data, str(current_user.id))
    
    return QuestionDetail(
        id=str(question.id),
        type=question.type,
        category=question.category,
        difficulty=question.difficulty,
        question=question.question,
        options=question.options,
        tags=question.tags,
        companies=question.companies,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        test_cases=question.test_cases
    )


@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user = Depends(get_current_user_from_token)
):
    """Get questions (without answers for students)"""
    questions = await AssessmentService.get_questions(type, category, difficulty, limit)
    
    return [
        QuestionResponse(
            id=str(q.id),
            type=q.type,
            category=q.category,
            difficulty=q.difficulty,
            question=q.question,
            options=q.options,
            tags=q.tags,
            companies=q.companies
        )
        for q in questions
    ]


@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment_data: AssessmentCreate,
    current_user = Depends(get_current_user_from_token)
):
    """Create a new assessment (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create assessments"
        )
    
    assessment = await AssessmentService.create_assessment(assessment_data, str(current_user.id))
    
    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        description=assessment.description,
        type=assessment.type,
        duration=assessment.duration,
        total_marks=assessment.total_marks,
        difficulty_level=assessment.difficulty_level,
        question_count=len(assessment.questions)
    )


@router.get("/assessments", response_model=List[AssessmentResponse])
async def get_assessments(
    limit: int = Query(50, le=100),
    current_user = Depends(get_current_user_from_token)
):
    """Get all available assessments"""
    assessments = await AssessmentService.get_assessments(limit)
    
    return [
        AssessmentResponse(
            id=str(a.id),
            title=a.title,
            description=a.description,
            type=a.type,
            duration=a.duration,
            total_marks=a.total_marks,
            difficulty_level=a.difficulty_level,
            question_count=len(a.questions)
        )
        for a in assessments
    ]


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Get assessment details"""
    assessment = await AssessmentService.get_assessment(assessment_id)
    
    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        description=assessment.description,
        type=assessment.type,
        duration=assessment.duration,
        total_marks=assessment.total_marks,
        difficulty_level=assessment.difficulty_level,
        question_count=len(assessment.questions)
    )


@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assessment(
    submission_data: SubmissionCreate,
    current_user = Depends(get_current_user_from_token)
):
    """Submit assessment answers"""
    submission = await AssessmentService.submit_assessment(
        str(current_user.id),
        submission_data
    )
    
    return SubmissionResponse(
        id=str(submission.id),
        assessment_id=submission.assessment_id,
        score=submission.score,
        coding_score=submission.coding_score,
        total_score=submission.total_score,
        accuracy=submission.accuracy,
        time_taken=submission.time_taken,
        submitted_at=submission.submitted_at.isoformat()
    )


@router.get("/submissions", response_model=List[SubmissionResponse])
async def get_my_submissions(
    limit: int = Query(20, le=100),
    current_user = Depends(get_current_user_from_token)
):
    """Get current user's submission history"""
    submissions = await AssessmentService.get_user_submissions(str(current_user.id), limit)
    
    return [
        SubmissionResponse(
            id=str(s.id),
            assessment_id=s.assessment_id,
            score=s.score,
            coding_score=s.coding_score,
            total_score=s.total_score,
            accuracy=s.accuracy,
            time_taken=s.time_taken,
            submitted_at=s.submitted_at.isoformat()
        )
        for s in submissions
    ]


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Delete a question (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete questions"
        )
    await AssessmentService.delete_question(question_id)
    return None


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Delete an assessment (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete assessments"
        )
    await AssessmentService.delete_assessment(assessment_id)
    return None


@router.get("/company/{company_id}/aptitude", response_model=AssessmentResponse)
async def get_company_aptitude_test(
    company_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Get or generate a 50-question aptitude test for a company"""
    assessment = await AssessmentService.create_company_aptitude_test(company_id, str(current_user.id))
    
    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        description=assessment.description,
        type=assessment.type,
        duration=assessment.duration,
        total_marks=assessment.total_marks,
        difficulty_level=assessment.difficulty_level,
        question_count=len(assessment.questions)
    )


@router.get("/{assessment_id}/questions", response_model=List[QuestionResponse])
async def get_assessment_questions(
    assessment_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Get specific questions for an assessment (without correct answers)"""
    questions = await AssessmentService.get_assessment_questions(assessment_id)
    
    return [
        QuestionResponse(
            id=str(q.id),
            type=q.type,
            category=q.category,
            difficulty=q.difficulty,
            question=q.question,
            options=q.options,
            sample_input=q.sample_input,
            sample_output=q.sample_output,
            test_cases_count=len(q.test_cases) if q.test_cases else 0,
            tags=q.tags,
            companies=q.companies
        )
        for q in questions
    ]


@router.get("/company/{company_id}/coding", response_model=AssessmentResponse)
async def get_company_coding_test(
    company_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Get or generate a coding test for a company"""
    assessment = await AssessmentService.create_company_coding_test(company_id, str(current_user.id))
    
    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        description=assessment.description,
        type=assessment.type,
        duration=assessment.duration,
        total_marks=assessment.total_marks,
        difficulty_level=assessment.difficulty_level,
        question_count=len(assessment.questions)
    )


@router.get("/company/{company_id}/technical", response_model=AssessmentResponse)
async def get_company_technical_test(
    company_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Get or generate a technical MCQ test for a company"""
    assessment = await AssessmentService.create_company_technical_test(company_id, str(current_user.id))
    
    return AssessmentResponse(
        id=str(assessment.id),
        title=assessment.title,
        description=assessment.description,
        type=assessment.type,
        duration=assessment.duration,
        total_marks=assessment.total_marks,
        difficulty_level=assessment.difficulty_level,
        question_count=len(assessment.questions)
    )


@router.post("/run", tags=["Coding"])
async def run_code(
    payload: dict,
    current_user = Depends(get_current_user_from_token)
):
    """Run code snippet against sample input (live testing)"""
    from app.services.judge0_service import Judge0Service
    
    code = payload.get("code")
    language = payload.get("language")
    stdin = payload.get("stdin")
    expected_output = payload.get("expected_output")
    
    if not code or not language:
        raise HTTPException(status_code=400, detail="Code and language required")
        
    result = await Judge0Service.execute_code(code, language, stdin, expected_output)
    return result

@router.post("/{assessment_id}/question/{question_id}/submit", tags=["Coding"])
async def submit_question_answer(
    assessment_id: str,
    question_id: str,
    payload: dict,
    current_user = Depends(get_current_user_from_token)
):
    """Evaluate and score a single coding question answer"""
    code = payload.get("code")
    language = payload.get("language")
    
    if not code or not language:
        raise HTTPException(status_code=400, detail="Code and language required")
        
    result = await AssessmentService.evaluate_single_question(
        assessment_id=assessment_id,
        question_id=question_id,
        code=code,
        language=language
    )
    return result
