from fastapi import APIRouter, Depends, status
from schemas.city_type import CreateCityDTO, UpdateCityDTO, GetAllCitiesDTO
from services.city_service import city_service

router = APIRouter(prefix="/city", tags=["City"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_city(body: CreateCityDTO):
    """
    Tạo thành phố mới.
    Body sẽ được validate tự động bởi CreateCityDTO.
    """
    return await city_service.create(body)

@router.get("", status_code=status.HTTP_200_OK)
async def get_all_cities(query_params: GetAllCitiesDTO = Depends()):
    """
    Lấy danh sách thành phố (có phân trang).
    Depends() giúp lấy page, limit, search từ URL Query String và map vào GetAllCitiesDTO.
    """
    return await city_service.get_all(query_params)

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_city_by_id(id: str):
    """
    Lấy chi tiết thành phố theo ID.
    """
    return await city_service.get_by_id(id)

@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_city(id: str, body: UpdateCityDTO):
    """
    Cập nhật thành phố.
    """
    return await city_service.update(id, body)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_city(id: str):
    """
    Xóa thành phố.
    """
    return await city_service.delete(id)