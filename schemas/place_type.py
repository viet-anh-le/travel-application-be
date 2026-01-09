from typing import List, Optional
from pydantic import BaseModel, Field

# 1. Sub-DTOs
class SectionDTO(BaseModel):
    title: str
    content: str
    images: List[str] = Field(default_factory=list)

class MenuItemDTO(BaseModel):
    item: str
    price: str

# 2. Create DTO
class CreatePlaceDTO(BaseModel):
    type: str
    city_id: str
    name: str
    description: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    opening_hours: Optional[str] = None

    sections: List[SectionDTO] = Field(default_factory=list)

    # FOOD
    price_range: Optional[str] = None
    menu: List[MenuItemDTO] = Field(default_factory=list)
    specialties: List[str] = Field(default_factory=list)

    # FESTIVAL
    event_date: Optional[str] = None
    event_location: Optional[str] = None

    # RELATED POSTS
    related_posts: List[str] = Field(default_factory=list)

# 3. Update DTO
# Tất cả field đều Optional để cho phép cập nhật từng phần
class UpdatePlaceDTO(BaseModel):
    type: Optional[str] = None
    city_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    opening_hours: Optional[str] = None

    sections: Optional[List[SectionDTO]] = None

    price_range: Optional[str] = None
    menu: Optional[List[MenuItemDTO]] = None
    specialties: Optional[List[str]] = None

    event_date: Optional[str] = None
    event_location: Optional[str] = None

    related_posts: Optional[List[str]] = None

# 4. Query Params DTOs
class GetAllPlacesDTO(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None
    city_id: Optional[str] = None  # Đã đổi cityId -> city_id
    type: Optional[str] = None

class GetByCityIdDTO(BaseModel):
    id: str
    page: int = 1
    limit: int = 10

class FilterPlace(BaseModel):
    city_id: Optional[str] = None # Đã đổi cityId -> city_id
    type: Optional[str] = None
    search: Optional[str] = None