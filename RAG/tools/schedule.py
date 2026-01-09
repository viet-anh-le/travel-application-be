from RAG.models.schedule_schema import ScheduleItem
from RAG.repositories.schedule_repository import ScheduleRepository
from RAG.config.mongodb import get_database_schedule
import json
from datetime import datetime

async def schedule_trip(trip_details):
    db = await get_database_schedule()
    schedule_repo = ScheduleRepository(db)
    schedule_repo.create_schedule(trip_details)
    print("Schedule created successfully.")


# if __name__ == "__main__":
#     sample_trip = """
#     {
#   "user_id": "user_123",
#   "trip_id": "trip_20251102_001",
#   "location": "Thành phố Hồ Chí Minh",
#   "duration_days": 1,
#   "start_date": "2025-11-02T00:00:00Z",
#   "end_date": "2025-11-02T23:59:59Z",
#   "weather_summary": {
#     "avg_temp": 27.0,
#     "condition": "Mưa rào nhẹ hoặc nắng hạt",
#     "notes": "Mang áo mưa nhẹ và giày thoải mái"
#   },
#   "itinerary": [
#     {
#       "day": 1,
#       "title": "Khám phá Sài Gòn trong một ngày",
#       "activities": [
#         {
#           "time_start": "08:00",
#           "time_end": "10:30",
#           "description": "Đi bộ dọc các con phố cổ Quận 1, ngắm kiến trúc và ghé cà phê",
#           "type": "Attraction"
#         },
#         {
#           "time_start": "11:00",
#           "time_end": "12:00",
#           "description": "Ăn trưa: phở hoặc bánh mì tại quán ăn đường phố",
#           "type": "Food"
#         },
#         {
#           "time_start": "13:00",
#           "time_end": "15:30",
#           "description": "Tham quan chợ, trung tâm thương mại hoặc công trình lịch sử tùy sở thích",
#           "type": "Attraction"
#         },
#         {
#           "time_start": "18:00",
#           "time_end": "20:00",
#           "description": "Bữa tối: bánh xèo, bún bò hoặc mì vịt tiềm tại quán địa phương",
#           "type": "Food"
#         },
#         {
#           "time_start": "20:30",
#           "time_end": "22:00",
#           "description": "Thưởng thức cà phê Sài Gòn truyền thống, kết thúc ngày",
#           "type": "Food"
#         }
#       ]
#     }
#   ],
#   "accommodation": {
#     "address": "19-23 Lam Son Square, Bến Nghé Ward, District 1, Thành phố Hồ Chí Minh",
#     "price_range": "mid-range",
#     "notes": "Khách sạn Rex Hotel Saigon, thuận tiện cho di chuyển"
#   },
#   "tips": [
#     "Mang áo mưa nhẹ và ô dù vì có khả năng mưa rào.",
#     "Đặt phòng và bàn ăn trước để tránh chờ đợi."
#   ]
# }
#     """
#     schedule_trip(sample_trip)
