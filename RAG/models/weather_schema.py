from pydantic import BaseModel, Field
from typing import Optional

class WeatherInput(BaseModel):
    """
    Schema đại diện cho dữ liệu đầu vào của hàm get_weather.
    """
    city: str = Field(..., description="Tên thành phố (Hanoi, Ho Chi Minh, hoặc Da Nang).")
    start_date: Optional[str] = Field(None, description="Ngày bắt đầu (định dạng YYYY-MM-DD).")
    end_date: Optional[str] = Field(None, description="Ngày kết thúc (định dạng YYYY-MM-DD).")
    lang: str = Field("vi", description="Ngôn ngữ hiển thị (mặc định: 'vi').")
