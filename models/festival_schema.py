from typing import List
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field

class Festival(Document):
    city_id: PydanticObjectId
    name: str
    description: str = ""
    start_date: datetime
    end_date: datetime
    
    image_urls: List[str] = Field(default_factory=list)

    class Settings:
        name = "festivals"