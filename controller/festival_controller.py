from fastapi import APIRouter, Depends, status
from services.festival_service import festival_service
from schemas.festival_type import (
    CreateFestivalDTO,
    UpdateFestivalDTO,
    GetAllFestivalsDTO
)

router = APIRouter(prefix="/festival", tags=["Festival"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_festival(body: CreateFestivalDTO):
    """
    Tạo lễ hội mới.
    """
    return await festival_service.create(body)

@router.get("", status_code=status.HTTP_200_OK)
async def get_all_festivals(query_params: GetAllFestivalsDTO = Depends()):
    """
    Lấy danh sách lễ hội (có phân trang).
    Sử dụng Depends() để map query string (page, limit) vào DTO.
    """
    return await festival_service.get_all(query_params)

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_festival_by_id(id: str):
    """
    Lấy chi tiết lễ hội theo ID.
    """
    return await festival_service.get_by_id(id)

@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_festival(id: str, body: UpdateFestivalDTO):
    """
    Cập nhật thông tin lễ hội.
    """
    return await festival_service.update(id, body)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_festival(id: str):
    """
    Xóa lễ hội.
    """
    return await festival_service.delete(id)