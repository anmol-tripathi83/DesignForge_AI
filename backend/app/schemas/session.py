from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.schemas.message import MessageResponse

class SessionCreate(BaseModel):
    problem_name: str = Field(..., min_length=1, max_length=100)

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    problem_name: str
    status: str  # 'in_progress', 'completed', 'abandoned'
    current_step: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: Optional[List["MessageResponse"]] = []

    class Config:
        from_attributes = True

class SessionDetailResponse(SessionResponse):
    messages: List["MessageResponse"] = []

# Forward reference for MessageResponse
from app.schemas.message import MessageResponse
SessionResponse.model_rebuild()
SessionDetailResponse.model_rebuild()