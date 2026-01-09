from datetime import datetime, timezone
from typing import Any, List, Literal
from pydantic import BaseModel, Field

# Một tin nhắn trong cuộc hội thoại
class ChatMessage(BaseModel):
    role: Literal["human", "ai"]
    content: str
    trip_id: Any = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Một phiên hội thoại hoàn chỉnh
class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
