from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, description="User response or prompt")

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str # user, assistant, system
    message: str
    suggested_replies: Optional[List[str]] = None
    updated_field_ids: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatTurnResult(BaseModel):
    assistant_reply: str
    suggested_replies: List[str] = []
    updated_fields: List[Dict[str, Any]] = []
    session_metrics: Optional[Dict[str, Any]] = None
