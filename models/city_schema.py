from typing import List
from beanie import Document
from pydantic import Field

class City(Document):
    name: str
    country: str
    description: str = ""
    image_urls: List[str] = Field(default_factory=list)

    class Settings:
        name = "cities"