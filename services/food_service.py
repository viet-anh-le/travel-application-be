import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
from typing import List

from beanie import PydanticObjectId
from beanie.operators import RegEx, Or

from models.food_schema import Food
from models.city_schema import City
from models.user_schema import User

from schemas.food_type import (
    CreateFoodDTO,
    UpdateFoodDTO,
    GetAllFoodsDTO,
    GetFoodByCityIdDTO,
    FoodCalendarRequest,
)
from core.error_response import BadRequestError, NotFoundError, UnauthorizedError
from core.success_response import OkResponse, CreatedResponse
from configs.google_calendar import get_calendar_service, oauth2_client

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class FoodService:

    async def _populate_city(self, food: Food):
        """Hàm phụ trợ để lấy thông tin city và map vào kết quả"""
        food_dict = food.model_dump()
        food_dict["id"] = str(food.id)

        city = await City.get(food.city_id)

        food_dict["city"] = city.model_dump() if city else None
        if "city_id" in food_dict:
            del food_dict["city_id"]

        return food_dict

    async def create(self, payload: CreateFoodDTO):
        if not PydanticObjectId.is_valid(payload.city_id):
            raise BadRequestError("Invalid City ID format")

        city = await City.get(PydanticObjectId(payload.city_id))
        if not city:
            raise BadRequestError("City not found")

        data = payload.model_dump()
        data["city_id"] = PydanticObjectId(payload.city_id)

        food = Food(**data)
        await food.create()

        return CreatedResponse("Food created successfully", food)

    async def get_all(self, query_params: GetAllFoodsDTO):
        search_criteria = []

        if hasattr(query_params, "search") and query_params.search:
            search_term = query_params.search
            search_criteria.append(
                Or(
                    RegEx(Food.name, search_term, "i"),
                    RegEx(Food.address, search_term, "i"),
                    RegEx(Food.description, search_term, "i"),
                )
            )

        if hasattr(query_params, "city_id") and query_params.city_id:
            if PydanticObjectId.is_valid(query_params.city_id):
                search_criteria.append(Food.city_id == PydanticObjectId(query_params.city_id))

        if search_criteria:
            query = Food.find(*search_criteria)
        else:
            query = Food.find_all()

        skip = (query_params.page - 1) * query_params.limit

        total_docs = await query.count()
        foods = await query.skip(skip).limit(query_params.limit).to_list()

        data = []
        for food in foods:
            data.append(await self._populate_city(food))

        pagination = {
            "total_docs": total_docs,
            "limit": query_params.limit,
            "page": query_params.page,
            "total_pages": (total_docs + query_params.limit - 1) // query_params.limit,
        }

        return OkResponse("Get all foods successfully", {"docs": data, "pagination": pagination})

    async def get_by_id(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        food = await Food.get(PydanticObjectId(id))
        if not food:
            raise NotFoundError("Food not found")

        data = await self._populate_city(food)
        return OkResponse("Get food successfully", data)

    async def get_by_city_id(self, payload: GetFoodByCityIdDTO):
        if not PydanticObjectId.is_valid(payload.id):
            raise BadRequestError("Invalid City ID format")

        query = Food.find(Food.city_id == PydanticObjectId(payload.id))

        skip = (payload.page - 1) * payload.limit
        total_docs = await query.count()
        foods = await query.skip(skip).limit(payload.limit).to_list()

        data = []
        for food in foods:
            data.append(await self._populate_city(food))

        pagination = {
            "total_docs": total_docs,
            "limit": payload.limit,
            "page": payload.page,
            "total_pages": (total_docs + payload.limit - 1) // payload.limit,
        }

        return OkResponse(
            "Get foods by city successfully", {"docs": data, "pagination": pagination}
        )

    async def update(self, id: str, payload: UpdateFoodDTO):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        food = await Food.get(PydanticObjectId(id))
        if not food:
            raise NotFoundError("Food not found")

        update_data = payload.model_dump(exclude_unset=True)

        if "city_id" in update_data:
            new_city_id = update_data["city_id"]
            if not PydanticObjectId.is_valid(new_city_id):
                raise BadRequestError("Invalid New City ID format")

            city = await City.get(PydanticObjectId(new_city_id))
            if not city:
                raise BadRequestError("City not found")

            update_data["city_id"] = PydanticObjectId(new_city_id)

        await food.set(update_data)

        updated_food = await Food.get(PydanticObjectId(id))
        data = await self._populate_city(updated_food)

        return OkResponse("Food updated successfully", data)

    async def delete(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        food = await Food.get(PydanticObjectId(id))
        if not food:
            raise NotFoundError("Food not found")

        await food.delete()
        return OkResponse("Food deleted successfully", food)

    async def create_calendar_event(self, food_id: str, payload: FoodCalendarRequest):
        if not PydanticObjectId.is_valid(payload.user_id):
            raise BadRequestError("Invalid User ID")

        user = await User.get(PydanticObjectId(payload.user_id))
        if not user:
            raise NotFoundError("User not found")

        if not PydanticObjectId.is_valid(food_id):
            raise BadRequestError("Invalid Food ID")

        food = await Food.get(PydanticObjectId(food_id))
        if not food:
            raise NotFoundError("Food not found")

        def get_auth_response():
            auth_url, _ = oauth2_client.authorization_url(
                prompt="consent",
                access_type="offline",
                state=str(user.id),
            )
            return OkResponse(
                "Yêu cầu liên kết Google Calendar", {"require_auth": True, "auth_url": auth_url}
            )

        gc_info = getattr(user, "google_calendar", None)
        if not gc_info or not gc_info.access_token:
            return get_auth_response()

        try:
            service = get_calendar_service(user)

            start_dt = payload.start_time
            end_dt = start_dt + timedelta(minutes=payload.duration_minutes)

            event_body = {
                "summary": f"Đi ăn: {food.name}",
                "location": food.address,
                "description": (
                    f"Thưởng thức món ngon tại {food.name}.\n"
                    f"Địa chỉ: {food.address}\n\n"
                    f"Ghi chú: {payload.note or 'Không có'}"
                ),
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "Asia/Ho_Chi_Minh",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "Asia/Ho_Chi_Minh",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 30},
                    ],
                },
                "colorId": "5",
            }
            event_result = service.events().insert(calendarId="primary", body=event_body).execute()

            return OkResponse(
                "Thêm lịch thành công",
                {
                    "event_id": event_result.get("id"),
                    "html_link": event_result.get("htmlLink"),
                    "summary": event_result.get("summary"),
                },
            )

        except Exception as e:
            print(f"Google Calendar Error (Re-auth required): {str(e)}")
            return get_auth_response()


food_service = FoodService()
