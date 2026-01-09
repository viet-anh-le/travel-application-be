from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CreateFestivalDTO(BaseModel):
    city_id: str
    name: str
    description: Optional[str] = ""
    start_date: datetime
    end_date: datetime
    image_urls: List[str] = Field(default_factory=list)

class UpdateFestivalDTO(BaseModel):
    city_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    image_urls: Optional[List[str]] = None

class GetAllFestivalsDTO(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None
    city_id: Optional[str] = None

class GetFestivalByCityIdDTO(BaseModel):
    id: str
    page: int = 1
    limit: int = 10