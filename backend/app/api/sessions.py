from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.auth import get_current_user_id
from app.models.session import InterviewSession
from app.models.message import Message
from app.schemas.session import SessionCreate, SessionResponse, SessionDetailResponse
from uuid import UUID

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all sessions for the authenticated user."""
    result = await db.execute(
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
    )
    sessions = result.scalars().all()

    return sessions

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new interview session."""
    new_session = InterviewSession(
        user_id=user_id,
        problem_name=session_data.problem_name,
        status="in_progress",
        current_step=0
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

     # Add welcome message
    welcome_msg = Message(
        session_id=new_session.id,
        role="assistant",
        content=f"👋 Welcome to your system design interview on **{new_session.problem_name}**!\n\nI'm your AI interviewer. Let's start with the first question.",
    )
    db.add(welcome_msg)
    
    # Add first question
    first_question = Message(
        session_id=new_session.id,
        role="assistant",
        content=f"**Question:** Describe the high-level architecture of **{new_session.problem_name}**. What are the main components and how do they interact?",
    )
    db.add(first_question)
    
    await db.commit()

    # Fetch session with messages
    result = await db.execute(
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.id == new_session.id)
    )   

    session = result.scalar_one()

    return session

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific session with all messages."""
    result = await db.execute(
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Ensure the session belongs to the current user
    if str(session.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    return session