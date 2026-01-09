from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from RAG.models.schedule_schema import Accommodation, WeatherSummary, Itinerary

class CreateScheduleRequest(BaseModel):
    user_id: str
    trip_id: str
    location: str
    duration_days: int
    start_date: datetime
    end_date: datetime
    trip_cover_image: Optional[str] = None
    accommodation: Optional[Accommodation] = None
    tips: Optional[List[str]] = None
    weather_summary: Optional[WeatherSummary] = None
    itinerary: List[Itinerary]

class UpdateScheduleRequest(BaseModel):
    location: Optional[str] = None
    duration_days: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    trip_cover_image: Optional[str] = None
    tips: Optional[List[str]] = None
    accommodation: Optional[Accommodation] = None
    weather_summary: Optional[WeatherSummary] = None
    itinerary: Optional[List[Itinerary]] = None

# Schema cho sự kiện Google Calendar gửi từ App lên
class GoogleCalendarEventRequest(BaseModel):
    summary: str
    location: Optional[str] = None
    description: Optional[str] = None
    start: dict # { "dateTime": "...", "timeZone": "..." }
    end: dict