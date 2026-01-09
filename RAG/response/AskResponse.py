from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class AskResponse(BaseModel):
    message: str
    answer: Any
    timestamp: Optional[datetime] = None
    
class ChatResponse(BaseModel):
    chat_history: str
    reformulated_question: list[str] = None
    final_answer: str