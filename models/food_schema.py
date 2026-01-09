from typing import List
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

class Section(BaseModel):
    title: str
    content: str
    images: List[str] = Field(default_factory=list)

class Food(Document):
    city_id: PydanticObjectId
    name: str
    description: str = ""
    type: str = "" 
    address: str = ""
    price_range: str = ""
    
    image_urls: List[str] = Field(default_factory=list)
    
    sections: List[Section] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "foods"