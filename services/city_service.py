from beanie import PydanticObjectId
from models.city_schema import City
from schemas.city_type import CreateCityDTO, UpdateCityDTO, GetAllCitiesDTO

from core.error_response import BadRequestError, NotFoundError
from core.success_response import OkResponse, CreatedResponse

class CityService:
    async def create(self, payload: CreateCityDTO):
        existing = await City.find_one({"name": payload.name})
        if existing:
            raise BadRequestError("City already exists")

        city = City(**payload.model_dump())
        await city.create()
        
        return CreatedResponse("City created successfully", city)

    async def get_all(self, query_params: GetAllCitiesDTO):
        query = City.find_all()

        skip = (query_params.page - 1) * query_params.limit
        
        total_docs = await query.count()
        cities = await query.skip(skip).limit(query_params.limit).to_list()

        pagination = {
            "total_docs": total_docs,
            "limit": query_params.limit,
            "page": query_params.page,
            "total_pages": (total_docs + query_params.limit - 1) // query_params.limit
        }

        return OkResponse("Get all cities successfully", {
            "docs": cities,
            "pagination": pagination
        })

    async def get_by_id(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        city = await City.get(PydanticObjectId(id))
        if not city:
            raise NotFoundError("City not found")
            
        return OkResponse("Get city successfully", city)

    async def update(self, id: str, payload: UpdateCityDTO):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        city = await City.get(PydanticObjectId(id))
        if not city:
            raise NotFoundError("City not found")

        update_data = payload.model_dump(exclude_unset=True)

        await city.set(update_data)
        
        return OkResponse("City updated successfully", city)

    async def delete(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        city = await City.get(PydanticObjectId(id))
        if not city:
            raise NotFoundError("City not found")

        await city.delete()
        
        return OkResponse("City deleted successfully", city)

city_service = CityService()