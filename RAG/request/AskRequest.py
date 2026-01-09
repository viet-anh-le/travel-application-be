from pydantic import BaseModel
from typing import Optional

class AskRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"