from fastapi import APIRouter, Depends, status, Query, Body
from services.food_service import food_service
from schemas.food_type import (
    CreateFoodDTO,
    UpdateFoodDTO,
    GetAllFoodsDTO,
    GetFoodByCityIdDTO,
    FoodCalendarRequest,
)

router = APIRouter(prefix="/food", tags=["Food"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_food(body: CreateFoodDTO):
    """
    Tạo món ăn mới.
    """
    return await food_service.create(body)


@router.get("/city/{city_id}", status_code=status.HTTP_200_OK)
async def get_foods_by_city(city_id: str, page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    """
    Lấy danh sách món ăn theo City ID.
    Route này phải đặt trước route /{id} để tránh conflict.
    """
    # Đóng gói dữ liệu vào DTO để gửi sang Service
    payload = GetFoodByCityIdDTO(id=city_id, page=page, limit=limit)
    return await food_service.get_by_city_id(payload)


@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_food_by_id(id: str):
    """
    Lấy chi tiết món ăn theo ID.
    """
    return await food_service.get_by_id(id)


@router.post("/{id}/google-calendar", status_code=status.HTTP_201_CREATED)
async def create_food_calendar_event(id: str, payload: FoodCalendarRequest = Body(...)):
    """
    Tạo sự kiện Google Calendar cho món ăn cụ thể.
    - id: ID của món ăn (để lấy tên, địa chỉ làm location)
    - payload: Chứa user_id, start_time, duration
    """
    return await food_service.create_calendar_event(food_id=id, payload=payload)


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_foods(query_params: GetAllFoodsDTO = Depends()):
    """
    Lấy tất cả món ăn (kèm search, filter, pagination).
    Sử dụng Depends() để map query string vào DTO.
    """
    return await food_service.get_all(query_params)


@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_food(id: str, body: UpdateFoodDTO):
    """
    Cập nhật thông tin món ăn.
    """
    return await food_service.update(id, body)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_food(id: str):
    """
    Xóa món ăn.
    """
    return await food_service.delete(id)
