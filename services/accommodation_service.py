from beanie import PydanticObjectId
from beanie.operators import RegEx, Or
from typing import List

from models.accommodation_schema import Accommodation
from models.city_schema import City
from schemas.accommodation_type import (
    CreateAccommodationDTO, 
    UpdateAccommodationDTO, 
    GetAllAccommodationsDTO
)
from core.error_response import BadRequestError, NotFoundError
from core.success_response import OkResponse, CreatedResponse

class AccommodationService:

    async def _populate_city(self, accommodation: Accommodation):
        """Hàm phụ trợ để lấy thông tin city và map vào kết quả"""
        acc_dict = accommodation.model_dump()
        
        acc_dict['id'] = str(accommodation.id)
        
        city = await City.get(accommodation.city_id)
        
        if city:
            acc_dict['city'] = {
                "id": str(city.id),
                "name": city.name,
                "country": city.country
            }
        else:
            acc_dict['city'] = None

        if 'city_id' in acc_dict:
            del acc_dict['city_id']
            
        return acc_dict

    async def create(self, payload: CreateAccommodationDTO):
        if not PydanticObjectId.is_valid(payload.city_id):
             raise BadRequestError("Invalid City ID format")

        city = await City.get(PydanticObjectId(payload.city_id))
        if not city:
            raise BadRequestError("City not found")

        existing = await Accommodation.find_one({
            "name": payload.name,
            "city_id": PydanticObjectId(payload.city_id)
        })
        
        if existing:
            raise BadRequestError("Accommodation already exists in this city")

        data = payload.model_dump()
        data['city_id'] = PydanticObjectId(payload.city_id)
        
        accommodation = Accommodation(**data)
        await accommodation.create()

        return CreatedResponse("Accommodation created successfully", accommodation)

    async def get_all(self, query_params: GetAllAccommodationsDTO):
        search_criteria = []
        if hasattr(query_params, 'search') and query_params.search:
            search_term = query_params.search
            search_criteria.append(
                Or(
                    RegEx(Accommodation.name, search_term, "i"),
                    RegEx(Accommodation.address, search_term, "i"),
                    RegEx(Accommodation.description, search_term, "i")
                )
            )
        if hasattr(query_params, 'city_id') and query_params.city_id:
            if PydanticObjectId.is_valid(query_params.city_id):
                search_criteria.append(Accommodation.city_id == PydanticObjectId(query_params.city_id))

        if search_criteria:
            query = Accommodation.find(*search_criteria)
        else:
            query = Accommodation.find_all()

        skip = (query_params.page - 1) * query_params.limit
        
        total_docs = await query.count()
        accommodations = await query.skip(skip).limit(query_params.limit).to_list()

        data = []
        for acc in accommodations:
            data.append(await self._populate_city(acc))

        pagination = {
            "total_docs": total_docs,
            "limit": query_params.limit,
            "page": query_params.page,
            "total_pages": (total_docs + query_params.limit - 1) // query_params.limit
        }

        return OkResponse("Get all accommodations successfully", {
            "docs": data,
            "pagination": pagination
        })

    async def get_by_id(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        accommodation = await Accommodation.get(PydanticObjectId(id))
        if not accommodation:
            raise NotFoundError("Accommodation not found")

        data = await self._populate_city(accommodation)
        return OkResponse("Get accommodation successfully", data)

    async def update(self, id: str, payload: UpdateAccommodationDTO):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        accommodation = await Accommodation.get(PydanticObjectId(id))
        if not accommodation:
            raise NotFoundError("Accommodation not found")

        update_data = payload.model_dump(exclude_unset=True)

        if 'city_id' in update_data:
            new_city_id = update_data['city_id']
            if not PydanticObjectId.is_valid(new_city_id):
                raise BadRequestError("Invalid New City ID format")
                
            city = await City.get(PydanticObjectId(new_city_id))
            if not city:
                raise BadRequestError("City not found")
            
            update_data['city_id'] = PydanticObjectId(new_city_id)

        await accommodation.set(update_data)
        
        updated_acc = await Accommodation.get(PydanticObjectId(id))
        data = await self._populate_city(updated_acc)
        
        return OkResponse("Accommodation updated successfully", data)

    async def delete(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        accommodation = await Accommodation.get(PydanticObjectId(id))
        if not accommodation:
            raise NotFoundError("Accommodation not found")

        await accommodation.delete()
        return OkResponse("Accommodation deleted successfully", accommodation)

accommodation_service = AccommodationService()