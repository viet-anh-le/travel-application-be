from typing import List
from beanie import PydanticObjectId
from beanie.operators import RegEx, In

# Import Models & DTOs
from models.place_schema import Place
from models.city_schema import City 
from schemas.place_type import (
    CreatePlaceDTO, 
    UpdatePlaceDTO, 
    GetAllPlacesDTO,
    GetByCityIdDTO
)
from core.error_response import BadRequestError, NotFoundError # Các class lỗi tùy chỉnh của bạn
from core.success_response import OkResponse, CreatedResponse

class PlaceService:
    
    async def _populate_city(self, place: Place):
        """Hàm phụ trợ để populate thông tin city vào kết quả trả về"""
        place_dict = place.model_dump()
        place_dict['id'] = str(place.id)
        
        city = await City.get(place.city_id)
        
        place_dict['city'] = city.model_dump() if city else None
        del place_dict['city_id']
        
        return place_dict

    async def create(self, payload: CreatePlaceDTO):
        city = await City.get(PydanticObjectId(payload.city_id))
        if not city:
            raise BadRequestError("City not found")

        existing_place = await Place.find_one({
            "name": payload.name,
            "city_id": PydanticObjectId(payload.city_id)
        })
        if existing_place:
            raise BadRequestError("Place already exists in this city")

        data = payload.model_dump()
        data['city_id'] = PydanticObjectId(payload.city_id)
        
        new_place = Place(**data)
        await new_place.create()

        return CreatedResponse("Place created successfully", new_place)

    async def get_all(self, query_params: GetAllPlacesDTO):
        # Tạo query filter
        search_criteria = []
        
        if query_params.search:
            # Tìm kiếm không phân biệt hoa thường (case-insensitive)
            search_criteria.append(RegEx(Place.name, query_params.search, "i"))
        
        if query_params.city_id:
            search_criteria.append(Place.city_id == PydanticObjectId(query_params.city_id))
            
        if query_params.type:
            search_criteria.append(Place.type == query_params.type)

        query = Place.find(*search_criteria)

        skip = (query_params.page - 1) * query_params.limit
        
        total_docs = await query.count()
        places = await query.skip(skip).limit(query_params.limit).to_list()

        data = []
        for place in places:
            data.append(await self._populate_city(place))

        pagination = {
            "total_docs": total_docs,
            "limit": query_params.limit,
            "page": query_params.page,
            "total_pages": (total_docs + query_params.limit - 1) // query_params.limit
        }

        return OkResponse("Get all places successfully", {
            "docs": data,
            "pagination": pagination
        })
        
    async def get_relevant_places(self, place_ids: List[str]):
        valid_ids = [
            PydanticObjectId(pid) 
            for pid in place_ids 
            if PydanticObjectId.is_valid(pid)
        ]

        if not valid_ids:
            return OkResponse("Get relevant places successfully", [])

        places = await Place.find(In(Place.id, valid_ids)).to_list()

        result = []
        for place in places:
            result.append(await self._populate_city(place))
        return OkResponse("Get relevant places successfully", result)

    async def get_by_id(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        place = await Place.get(PydanticObjectId(id))
        if not place:
            raise NotFoundError("Place not found")

        data = await self._populate_city(place)
        return OkResponse("Get place successfully", data)

    async def get_by_city_id(self, payload: GetByCityIdDTO):
        if not PydanticObjectId.is_valid(payload.id):
             raise BadRequestError("Invalid City ID format")
             
        query = Place.find(Place.city_id == PydanticObjectId(payload.id))
        
        skip = (payload.page - 1) * payload.limit
        total_docs = await query.count()
        places = await query.skip(skip).limit(payload.limit).to_list()
        
        data = []
        for place in places:
            data.append(await self._populate_city(place))
            
        pagination = {
            "total_docs": total_docs,
            "limit": payload.limit,
            "page": payload.page,
            "total_pages": (total_docs + payload.limit - 1) // payload.limit
        }
        
        return OkResponse("Get places by city successfully", {
            "docs": data,
            "pagination": pagination
        })

    async def update(self, id: str, payload: UpdatePlaceDTO):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        place = await Place.get(PydanticObjectId(id))
        if not place:
            raise NotFoundError("Place not found")

        update_data = payload.model_dump(exclude_unset=True)

        if 'city_id' in update_data:
            new_city_id = update_data['city_id']
            city = await City.get(PydanticObjectId(new_city_id))
            if not city:
                raise BadRequestError("New city not found")
            update_data['city_id'] = PydanticObjectId(new_city_id)

        await place.set(update_data)
        
        updated_place = await Place.get(PydanticObjectId(id))
        data = await self._populate_city(updated_place)
        
        return OkResponse("Place updated successfully", data)

    async def delete(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        place = await Place.get(PydanticObjectId(id))
        if not place:
            raise NotFoundError("Place not found")

        await place.delete()
        return OkResponse("Place deleted successfully")

place_service = PlaceService()