from typing import List
from beanie import Document, PydanticObjectId
from pydantic import Field

class Accommodation(Document):
    city_id: PydanticObjectId
    name: str
    description: str = ""
    type: str = "" 
    address: str = ""
    price_range: str = ""
    
    ratings: float = 0 
    
    image_urls: List[str] = Field(default_factory=list)

    class Settings:
        name = "accommodations"