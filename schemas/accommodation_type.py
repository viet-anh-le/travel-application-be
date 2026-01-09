from typing import List, Optional
from pydantic import BaseModel, Field

class CreateAccommodationDTO(BaseModel):
    city_id: str
    name: str
    description: Optional[str] = ""
    type: Optional[str] = ""
    address: Optional[str] = ""
    price_range: Optional[str] = ""
    ratings: Optional[float] = 0
    image_urls: List[str] = Field(default_factory=list)

class UpdateAccommodationDTO(BaseModel):
    city_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    price_range: Optional[str] = None
    ratings: Optional[float] = None
    image_urls: Optional[List[str]] = None

class GetAllAccommodationsDTO(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None
    city_id: Optional[str] = None
    type: Optional[str] = None
    min_rating: Optional[float] = None

class GetAccommodationByCityIdDTO(BaseModel):
    id: str
    page: int = 1
    limit: int = 10