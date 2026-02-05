from fastapi import APIRouter, Query, Path, Body, status
from typing import List, Optional
import datetime

from services.schedule_service import schedule_service
from schemas.schedule_type import (
    CreateScheduleRequest,
    UpdateScheduleRequest,
    GoogleCalendarEventRequest,
)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_schedule(payload: CreateScheduleRequest = Body(...)):
    """
    Tạo mới một lịch trình (Schedule).
    """
    return await schedule_service.create(payload)


@router.get("/")
async def get_all_schedules(
    page: int = Query(1, ge=1, description="Số trang"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng item mỗi trang"),
):
    """
    Lấy danh sách tất cả lịch trình có phân trang.
    """
    return await schedule_service.get_all(page, limit)


@router.get("/user/{user_id}")
async def get_schedules_by_user(
    user_id: str = Path(..., description="ID của người dùng"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên hoạt động trong lịch trình"),
    from_date: Optional[datetime.datetime] = Query(None, description="Lọc từ ngày (ISO format)"),
    to_date: Optional[datetime.datetime] = Query(None, description="Lọc đến ngày (ISO format)"),
):
    """
    Lấy danh sách lịch trình của một user cụ thể.
    Hỗ trợ tìm kiếm và lọc theo khoảng thời gian tạo.
    """
    return await schedule_service.get_by_user_id(
        user_id=user_id, page=page, limit=limit, search=search, from_date=from_date, to_date=to_date
    )


@router.get("/{id}")
async def get_schedule_by_id(id: str = Path(..., description="ID của lịch trình")):
    """
    Lấy thông tin chi tiết của một lịch trình.
    """
    return await schedule_service.get_by_id(id)


@router.put("/{id}")
async def update_schedule(
    id: str = Path(..., description="ID của lịch trình cần sửa"),
    payload: UpdateScheduleRequest = Body(...),
):
    """
    Cập nhật thông tin lịch trình.
    """
    return await schedule_service.update(id, payload)


@router.delete("/{id}")
async def delete_schedule(id: str = Path(..., description="ID của lịch trình cần xóa")):
    """
    Xóa vĩnh viễn một lịch trình.
    """
    return await schedule_service.delete(id)


@router.post("/google-calendar/{id}")
async def sync_google_calendar(
    id: str = Path(..., description="ID của lịch trình"),
    user_id: str = Query(..., description="ID của user thực hiện (cần token Google)"),
    events: List[GoogleCalendarEventRequest] = Body(
        ..., description="Danh sách các sự kiện cần tạo"
    ),
):
    """
    Đẩy các sự kiện trong lịch trình lên Google Calendar của user.
    Hệ thống sẽ tự động gửi email thông báo sau khi hoàn tất.
    """
    return await schedule_service.create_event_google_calendar(
        schedule_id=id, user_id=user_id, events=events
    )
