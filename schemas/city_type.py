from typing import List, Optional
from pydantic import BaseModel, Field

# DTO dùng để tạo mới City
class CreateCityDTO(BaseModel):
    name: str
    country: str
    description: Optional[str] = ""
    image_urls: List[str] = Field(default_factory=list)

# DTO dùng để cập nhật City (tất cả đều optional)
class UpdateCityDTO(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None

# DTO dùng cho query params (lấy danh sách)
class GetAllCitiesDTO(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None