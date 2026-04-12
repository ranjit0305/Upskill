from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.mock_interview import (
    MockInterviewAnswerItemResponse,
    MockInterviewAnswerRequest,
    MockInterviewAnswerResponse,
    MockInterviewFeedbackResponse,
    MockInterviewHistoryItem,
    MockInterviewHistoryResponse,
    MockInterviewQuestionResponse,
    MockInterviewSectionScoreResponse,
    MockInterviewSessionResponse,
    MockInterviewStartRequest,
)
from app.services.auth_service import AuthService
from app.services.mock_interview_service import MockInterviewService


router = APIRouter(prefix="/mock-interview", tags=["Mock Interview"])
security = HTTPBearer()


async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await AuthService.get_current_user(credentials.credentials)


def _serialize_question(question, index: int):
    if not question:
        return None
    return MockInterviewQuestionResponse(
        index=index,
        category=question.category,
        prompt=question.prompt,
        topic=question.topic,
        difficulty=question.difficulty,
        source=question.source,
    )


def _serialize_session(session) -> MockInterviewSessionResponse:
    current_question = None
    if session.status == "active" and session.current_question_index < len(session.questions):
        current_question = _serialize_question(
            session.questions[session.current_question_index],
            session.current_question_index,
        )

    return MockInterviewSessionResponse(
        id=str(session.id),
        mode=session.mode,
        status=session.status,
        company_id=session.company_id,
        company_name=session.company_name,
        current_question_index=session.current_question_index,
        total_questions=len(session.questions),
        current_question=current_question,
        section_scores=MockInterviewSectionScoreResponse(
            hr=session.section_scores.hr,
            technical=session.section_scores.technical,
            coding=session.section_scores.coding,
        ),
        overall_score=session.overall_score,
        summary=session.summary,
        recommendations=session.recommendations,
        comparison_summary=session.comparison_summary,
        improved_areas=session.improved_areas,
        focus_areas=session.focus_areas,
        answers=[
            MockInterviewAnswerItemResponse(
                question_index=answer.question_index,
                category=answer.category,
                prompt=answer.prompt,
                topic=answer.topic,
                answer=answer.answer,
                feedback=MockInterviewFeedbackResponse(
                    relevance=answer.feedback.relevance,
                    clarity=answer.feedback.clarity,
                    structure=answer.feedback.structure,
                    technical_accuracy=answer.feedback.technical_accuracy,
                    confidence=answer.feedback.confidence,
                    score=answer.feedback.score,
                    strengths=answer.feedback.strengths,
                    improvements=answer.feedback.improvements,
                    suggested_answer=answer.feedback.suggested_answer,
                ),
                answered_at=answer.answered_at.isoformat(),
            )
            for answer in session.answers
        ],
        started_at=session.started_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )


@router.post("/sessions", response_model=MockInterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_mock_interview(
    payload: MockInterviewStartRequest,
    current_user=Depends(get_current_user_from_token),
):
    session = await MockInterviewService.start_session(
        user_id=str(current_user.id),
        mode=payload.mode,
        company_id=payload.company_id,
        question_count=payload.question_count,
    )
    return _serialize_session(session)


@router.get("/sessions/{session_id}", response_model=MockInterviewSessionResponse)
async def get_mock_interview_session(
    session_id: str,
    current_user=Depends(get_current_user_from_token),
):
    session = await MockInterviewService.get_session(session_id, str(current_user.id))
    return _serialize_session(session)


@router.post("/sessions/{session_id}/answers", response_model=MockInterviewAnswerResponse)
async def submit_mock_interview_answer(
    session_id: str,
    payload: MockInterviewAnswerRequest,
    current_user=Depends(get_current_user_from_token),
):
    result = await MockInterviewService.submit_answer(
        session_id=session_id,
        user_id=str(current_user.id),
        answer_text=payload.answer,
    )
    feedback = result["feedback"]
    return MockInterviewAnswerResponse(
        session=_serialize_session(result["session"]),
        feedback=MockInterviewFeedbackResponse(
            relevance=feedback.relevance,
            clarity=feedback.clarity,
            structure=feedback.structure,
            technical_accuracy=feedback.technical_accuracy,
            confidence=feedback.confidence,
            score=feedback.score,
            strengths=feedback.strengths,
            improvements=feedback.improvements,
            suggested_answer=feedback.suggested_answer,
        ),
        next_question=_serialize_question(
            result["next_question"],
            result["session"].current_question_index,
        ) if result["next_question"] else None,
        completed=result["completed"],
    )


@router.post("/sessions/{session_id}/finish", response_model=MockInterviewSessionResponse)
async def finish_mock_interview(
    session_id: str,
    current_user=Depends(get_current_user_from_token),
):
    session = await MockInterviewService.finish_session(session_id, str(current_user.id))
    return _serialize_session(session)


@router.get("/history", response_model=MockInterviewHistoryResponse)
async def get_mock_interview_history(
    limit: int = Query(10, ge=1, le=30),
    company_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user_from_token),
):
    sessions = await MockInterviewService.get_history(str(current_user.id), limit, company_id=company_id)
    return MockInterviewHistoryResponse(
        sessions=[
            MockInterviewHistoryItem(
                id=str(session.id),
                mode=session.mode,
                status=session.status,
                company_name=session.company_name,
                overall_score=session.overall_score,
                started_at=session.started_at.isoformat(),
                completed_at=session.completed_at.isoformat() if session.completed_at else None,
                total_questions=len(session.questions),
                answered_questions=len(session.answers),
            )
            for session in sessions
        ]
    )
