from fastapi import APIRouter, Depends, status
from services.accommodation_service import accommodation_service
from schemas.accommodation_type import (
    CreateAccommodationDTO,
    UpdateAccommodationDTO,
    GetAllAccommodationsDTO
)

router = APIRouter(prefix="/accommodation", tags=["Accommodation"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_accommodation(body: CreateAccommodationDTO):
    """
    Tạo cơ sở lưu trú mới.
    """
    return await accommodation_service.create(body)

@router.get("", status_code=status.HTTP_200_OK)
async def get_all_accommodations(query_params: GetAllAccommodationsDTO = Depends()):
    """
    Lấy danh sách cơ sở lưu trú (có phân trang, lọc).
    Sử dụng Depends() để map query string vào DTO.
    """
    return await accommodation_service.get_all(query_params)

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_accommodation_by_id(id: str):
    """
    Lấy chi tiết cơ sở lưu trú theo ID.
    """
    return await accommodation_service.get_by_id(id)

@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_accommodation(id: str, body: UpdateAccommodationDTO):
    """
    Cập nhật thông tin cơ sở lưu trú.
    """
    return await accommodation_service.update(id, body)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_accommodation(id: str):
    """
    Xóa cơ sở lưu trú.
    """
    return await accommodation_service.delete(id)