from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SectionDTO(BaseModel):
    title: str
    content: str
    images: List[str] = Field(default_factory=list)


class CreateFoodDTO(BaseModel):
    city_id: str
    name: str
    description: Optional[str] = ""
    type: Optional[str] = ""
    address: Optional[str] = ""
    price_range: Optional[str] = ""
    image_urls: List[str] = Field(default_factory=list)
    sections: List[SectionDTO] = Field(default_factory=list)


class UpdateFoodDTO(BaseModel):
    city_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    price_range: Optional[str] = None
    image_urls: Optional[List[str]] = None
    sections: Optional[List[SectionDTO]] = None


class GetAllFoodsDTO(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None
    city_id: Optional[str] = None
    type: Optional[str] = None


class GetFoodByCityIdDTO(BaseModel):
    id: str
    page: int = 1
    limit: int = 10


class FoodCalendarRequest(BaseModel):
    user_id: str
    start_time: datetime
    duration_minutes: int = 90
    note: Optional[str] = None
