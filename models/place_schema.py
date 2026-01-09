from typing import List, Optional
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

class Section(BaseModel):
    title: str
    content: str
    images: List[str] = Field(default_factory=list)

class MenuItem(BaseModel):
    item: str
    price: str

class Place(Document):
    type: str  
    city_id: PydanticObjectId
    name: str
    description: str = ""
    image_urls: List[str] = Field(default_factory=list)
    opening_hours: str = ""
    
    sections: List[Section] = Field(default_factory=list)
    
    price_range: str = ""
    
    menu: List[MenuItem] = Field(default_factory=list)
    
    specialties: List[str] = Field(default_factory=list)
    event_date: Optional[str] = ""
    event_location: Optional[str] = ""
    related_posts: List[PydanticObjectId] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "places"