from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str  # 'user' or 'assistant'
    content: str
    score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True