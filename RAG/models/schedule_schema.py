from typing import List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from beanie import Document, Link, PydanticObjectId  
from models.user_schema import User 

class WeatherSummary(BaseModel):
    avg_temp: Optional[float] = None
    condition: Optional[str] = None
    notes: Optional[str] = None

class Activity(BaseModel):
    time_start: str
    time_end: str
    description: str
    type: Literal["Food", "Attraction", "Accommodation", "Festival", "Transport", "Other"] = "Other" 

class Itinerary(BaseModel):
    day: int
    title: str
    activities: List[Activity]

class Accommodation(BaseModel): 
    name: str
    address: str
    price_range: str
    notes: Optional[str] = None

class ScheduleItem(Document): 
    user_id: PydanticObjectId
    trip_id: PydanticObjectId
    location: str
    duration_days: int
    start_date: datetime
    end_date: datetime
    weather_summary: Optional[WeatherSummary] = None 
    itinerary: List[Itinerary] = []
    accommodation: Optional[Accommodation] = None
    tips: List[str] = []
    
    trip_cover_image: Optional[str] = None
    is_schedule_completed: bool = False 

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "schedules" 