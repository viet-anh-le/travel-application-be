from typing import Optional, Annotated, List
from beanie import Document, Indexed
from pydantic import BaseModel, Field
from constants.index import AUTH_PROVIDER, ROLE

class GoogleCalendar(BaseModel):
    email: str = ""
    access_token: str = ""
    refresh_token: str = ""
    scope: List[str] = Field(default_factory=list)
    token_type: str = ""
    expiry_date: Optional[int] = None

class User(Document):
    full_name: str = ""
    email: Annotated[str, Indexed(unique=True)]
    password: Optional[str] = None
    address: str = ""
    avatar: str = ""
    google_id: Optional[str] = None
    auth_provider: str = AUTH_PROVIDER.EMAIL
    role: str = ROLE.USER
    bio: str = ""
    google_calendar: GoogleCalendar = Field(default_factory=GoogleCalendar)
    
    class Settings:
        name = "users"