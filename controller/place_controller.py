from typing import List
from fastapi import APIRouter, Depends, status, Query
from services.place_service import place_service
from schemas.place_type import (
    CreatePlaceDTO, 
    UpdatePlaceDTO, 
    GetAllPlacesDTO, 
    GetByCityIdDTO
)

router = APIRouter(prefix="/place", tags=["Place"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_place(body: CreatePlaceDTO):
    """
    Tạo địa điểm mới.
    """
    return await place_service.create(body)

@router.get("/relevant", status_code=status.HTTP_200_OK)
async def get_relevant_places(place_ids: List[str] = Query(default=[])):
    """
    Lấy danh sách địa điểm theo danh sách ID.
    URL ví dụ: /api/places/relevant?place_ids=abc&place_ids=xyz
    """
    return await place_service.get_relevant_places(place_ids)

@router.get("/city/{city_id}", status_code=status.HTTP_200_OK)
async def get_places_by_city(
    city_id: str, 
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1)
):
    """
    Lấy danh sách địa điểm thuộc về 1 thành phố cụ thể.
    Kết hợp Path Param (city_id) và Query Param (page, limit).
    """
    payload = GetByCityIdDTO(id=city_id, page=page, limit=limit)
    return await place_service.get_by_city_id(payload)

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_place_by_id(id: str):
    """
    Lấy chi tiết địa điểm theo ID.
    """
    return await place_service.get_by_id(id)

@router.get("", status_code=status.HTTP_200_OK)
async def get_all_places(query_params: GetAllPlacesDTO = Depends()):
    """
    Lấy tất cả địa điểm (có search, filter, pagination).
    Sử dụng Depends() để tự động map query string vào GetAllPlacesDTO.
    """
    return await place_service.get_all(query_params)

@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_place(id: str, body: UpdatePlaceDTO):
    """
    Cập nhật địa điểm.
    """
    return await place_service.update(id, body)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_place(id: str):
    """
    Xóa địa điểm.
    """
    return await place_service.delete(id)