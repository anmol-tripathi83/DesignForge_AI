from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from app.core.database import get_db
from app.api.auth import get_current_user_id
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["Interview"])

class AnswerRequest(BaseModel):
    answer: str

class AnswerResponse(BaseModel):
    feedback: str
    next_question: str
    is_complete: bool
    architecture_summary: str | None = None

@router.post("/{session_id}/ask", response_model=AnswerResponse)
async def ask_question(
    session_id: UUID,
    request: AnswerRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an answer for the current question.
    Returns AI feedback and the next question (or architecture summary).
    """
    service = InterviewService(db)
    try:
        result = await service.process_answer(session_id, request.answer)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))