import os
from datetime import timedelta
from fastapi import HTTPException
from beanie import PydanticObjectId
from typing import List
from beanie.operators import RegEx, Or

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

# Import Models & Schemas
from models.festival_schema import Festival
from models.city_schema import City
from schemas.festival_type import (
    CreateFestivalDTO,
    UpdateFestivalDTO,
    GetAllFestivalsDTO,
    FestivalCalendarRequest,
)
from models.user_schema import User

# Import Error & Success Responses
from core.error_response import BadRequestError, NotFoundError, UnauthorizedError
from core.success_response import OkResponse, CreatedResponse

from configs.google_calendar import get_calendar_service, oauth2_client


class FestivalService:
    async def _populate_city(self, festival: Festival):
        """Hàm phụ trợ để lấy thông tin city và map vào kết quả"""
        festival_dict = festival.model_dump()
        festival_dict["id"] = str(festival.id)

        city = await City.get(festival.city_id)

        if city:
            festival_dict["city"] = {
                "name": city.name,
                "country": city.country,
                "_id": str(city.id),
            }
        else:
            festival_dict["city"] = None

        if "city_id" in festival_dict:
            del festival_dict["city_id"]

        return festival_dict

    async def create(self, payload: CreateFestivalDTO):
        if not PydanticObjectId.is_valid(payload.city_id):
            raise BadRequestError("Invalid City ID format")

        city = await City.get(PydanticObjectId(payload.city_id))
        if not city:
            raise BadRequestError("City not found")

        existing = await Festival.find_one(
            {"name": payload.name, "city_id": PydanticObjectId(payload.city_id)}
        )
        if existing:
            raise BadRequestError("Festival already exists in this city")

        data = payload.model_dump()
        data["city_id"] = PydanticObjectId(payload.city_id)

        festival = Festival(**data)
        await festival.create()

        return CreatedResponse("Festival created successfully", festival)

    async def get_all(self, query_params: GetAllFestivalsDTO):
        search_criteria = []
        if hasattr(query_params, "search") and query_params.search:
            search_term = query_params.search
            search_criteria.append(
                Or(
                    RegEx(Festival.name, search_term, "i"),
                    RegEx(Festival.description, search_term, "i"),
                )
            )
        if hasattr(query_params, "city_id") and query_params.city_id:
            if PydanticObjectId.is_valid(query_params.city_id):
                search_criteria.append(Festival.city_id == PydanticObjectId(query_params.city_id))
        if search_criteria:
            query = Festival.find(*search_criteria)
        else:
            query = Festival.find_all()

        skip = (query_params.page - 1) * query_params.limit

        total_docs = await query.count()
        festivals = await query.sort(Festival.id).skip(skip).limit(query_params.limit).to_list()

        data = []
        for fest in festivals:
            data.append(await self._populate_city(fest))

        pagination = {
            "total_docs": total_docs,
            "limit": query_params.limit,
            "page": query_params.page,
            "total_pages": (total_docs + query_params.limit - 1) // query_params.limit,
        }

        return OkResponse(
            "Get all festivals successfully", {"docs": data, "pagination": pagination}
        )

    async def get_by_id(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        festival = await Festival.get(PydanticObjectId(id))
        if not festival:
            raise NotFoundError("Festival not found")

        data = await self._populate_city(festival)
        return OkResponse("Get festival successfully", data)

    async def update(self, id: str, payload: UpdateFestivalDTO):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        festival = await Festival.get(PydanticObjectId(id))
        if not festival:
            raise NotFoundError("Festival not found")

        update_data = payload.model_dump(exclude_unset=True)

        if "city_id" in update_data:
            new_city_id = update_data["city_id"]
            if not PydanticObjectId.is_valid(new_city_id):
                raise BadRequestError("Invalid New City ID format")

            city = await City.get(PydanticObjectId(new_city_id))
            if not city:
                raise BadRequestError("City not found")

            update_data["city_id"] = PydanticObjectId(new_city_id)

        await festival.set(update_data)

        updated_festival = await Festival.get(PydanticObjectId(id))
        data = await self._populate_city(updated_festival)

        return OkResponse("Festival updated successfully", data)

    async def delete(self, id: str):
        if not PydanticObjectId.is_valid(id):
            raise BadRequestError("Invalid ID format")

        festival = await Festival.get(PydanticObjectId(id))
        if not festival:
            raise NotFoundError("Festival not found")

        await festival.delete()
        return OkResponse("Festival deleted successfully", festival)

    async def create_calendar_event(self, festival_id: str, payload: FestivalCalendarRequest):
        if not PydanticObjectId.is_valid(festival_id):
            raise BadRequestError("Invalid Festival ID")

        festival = await Festival.get(PydanticObjectId(festival_id))
        if not festival:
            raise NotFoundError("Lễ hội không tồn tại")

        city_name = "Việt Nam"
        if festival.city_id:
            city = await City.get(festival.city_id)
            if city:
                city_name = f"{city.name}, Việt Nam"

        if not PydanticObjectId.is_valid(payload.user_id):
            raise BadRequestError("Invalid User ID")

        user = await User.get(PydanticObjectId(payload.user_id))
        if not user:
            raise NotFoundError("User not found")

        def get_auth_response():
            auth_url, _ = oauth2_client.authorization_url(
                prompt="consent", access_type="offline", state=str(user.id)
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
                "summary": f"Tham gia: {festival.name}",
                "location": city_name,
                "description": (
                    f"Tham gia lễ hội {festival.name}.\n"
                    f"Thời gian diễn ra: {festival.start_date} - {festival.end_date}\n\n"
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
                        {"method": "popup", "minutes": 60},
                        {"method": "popup", "minutes": 1440},
                    ],
                },
                "colorId": "3",
            }

            event = service.events().insert(calendarId="primary", body=event_body).execute()

            return OkResponse(
                "Đã thêm lịch lễ hội thành công",
                {
                    "event_id": event.get("id"),
                    "html_link": event.get("htmlLink"),
                    "summary": event.get("summary"),
                },
            )

        except Exception as e:
            print(f"Calendar Error (Re-auth required): {e}")
            return get_auth_response()


festival_service = FestivalService()
