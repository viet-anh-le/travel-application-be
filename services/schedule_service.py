from pathlib import Path
from dotenv import load_dotenv
import os
import datetime
from datetime import timedelta
from typing import List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

from fastapi import HTTPException
from beanie import PydanticObjectId
from beanie.operators import In

from RAG.models.schedule_schema import ScheduleItem
from models.user_schema import User
from schemas.schedule_type import (
    CreateScheduleRequest,
    UpdateScheduleRequest,
    GoogleCalendarEventRequest,
)
from configs.mailer import send_google_add_schedule_email

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def success_response(message: str, data: any = None):
    return {"message": message, "data": data}


class ScheduleService:
    async def create(self, payload: CreateScheduleRequest):
        try:
            user_oid = PydanticObjectId(payload.user_id)
            user = await User.get(user_oid)
        except:
            user = None

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        new_schedule = ScheduleItem(
            user_id=user.id,
            trip_id=payload.trip_id,
            location=payload.location,
            duration_days=payload.duration_days,
            start_date=payload.start_date,
            end_date=payload.end_date,
            trip_cover_image=payload.trip_cover_image,
            accommodation=payload.accommodation,
            weather_summary=payload.weather_summary,
            itinerary=payload.itinerary,
            tips=payload.tips or [],
        )

        await new_schedule.insert()

        res_dict = new_schedule.model_dump()
        res_dict["id"] = str(new_schedule.id)
        res_dict["user_id"] = str(new_schedule.user_id)

        return success_response("Schedule created successfully", res_dict)

    async def get_all(self, page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        schedules_cursor = ScheduleItem.find().sort("-created_at").skip(skip).limit(limit)
        schedules = await schedules_cursor.to_list()

        results = []

        if schedules:
            user_ids = [s.user_id for s in schedules if s.user_id]
            users = await User.find(In(User.id, user_ids)).to_list()
            user_map = {u.id: u for u in users}

            for schedule in schedules:
                schedule_dict = schedule.model_dump()
                schedule_dict["id"] = str(schedule.id)  # Fix ID Schedule

                # Manual Populate User
                if schedule.user_id in user_map:
                    user_obj = user_map[schedule.user_id]
                    user_dict = user_obj.model_dump(exclude={"password"})
                    user_dict["id"] = str(user_obj.id)  # Fix ID User
                    schedule_dict["user_id"] = user_dict
                else:
                    schedule_dict["user_id"] = str(schedule.user_id)

                if "trip_id" in schedule_dict:
                    schedule_dict["trip_id"] = str(schedule_dict["trip_id"])

                results.append(schedule_dict)

        total_docs = await ScheduleItem.find().count()
        total_pages = (total_docs + limit - 1) // limit

        return success_response(
            "Get all schedules successfully",
            {
                "docs": results,
                "pagination": {
                    "totalDocs": total_docs,
                    "limit": limit,
                    "page": page,
                    "totalPages": total_pages,
                },
            },
        )

    async def get_by_user_id(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
    ):
        skip = (page - 1) * limit
        try:
            u_oid = PydanticObjectId(user_id)
        except:
            return success_response("Invalid User ID", {"docs": [], "pagination": {}})

        current_user = await User.get(u_oid)

        user_info = None
        if current_user:
            user_info = current_user.model_dump(exclude={"password"})
            user_info["id"] = str(current_user.id)

        query_filters = [ScheduleItem.user_id == u_oid]

        if search:
            query_filters.append(
                {"itinerary": {"$elemMatch": {"title": {"$regex": search, "$options": "i"}}}}
            )

        if from_date and to_date:
            next_day = to_date + timedelta(days=1)
            query_filters.append(ScheduleItem.created_at >= from_date)
            query_filters.append(ScheduleItem.created_at <= next_day)

        find_query = ScheduleItem.find(*query_filters).sort("-created_at")
        total_docs = await find_query.count()
        schedules = await find_query.skip(skip).limit(limit).to_list()

        results = []
        if schedules:
            for schedule in schedules:
                schedule_dict = schedule.model_dump()

                schedule_dict["id"] = str(schedule.id)

                if "trip_id" in schedule_dict:
                    schedule_dict["trip_id"] = str(schedule_dict["trip_id"])

                if user_info:
                    schedule_dict["user_id"] = user_info
                else:
                    schedule_dict["user_id"] = str(schedule.user_id)

                results.append(schedule_dict)

        total_pages = (total_docs + limit - 1) // limit

        return success_response(
            "Get all schedules by user successfully",
            {
                "docs": results,
                "pagination": {
                    "totalDocs": total_docs,
                    "limit": limit,
                    "page": page,
                    "totalPages": total_pages,
                },
            },
        )

    async def get_by_id(self, id: str):
        try:
            oid = PydanticObjectId(id)
        except:
            raise HTTPException(status_code=404, detail="Invalid ID format")

        schedule = await ScheduleItem.get(oid)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        schedule_dict = schedule.model_dump()
        schedule_dict["_id"] = str(schedule.id)
        if "trip_id" in schedule_dict:
            schedule_dict["trip_id"] = str(schedule_dict["trip_id"])

        if schedule.user_id:
            user = await User.get(schedule.user_id)
            if user:
                user_dict = user.model_dump(exclude={"password"})
                user_dict["id"] = str(user.id)
                schedule_dict["user_id"] = user_dict
            else:
                schedule_dict["user_id"] = str(schedule.user_id)

        return success_response("Get schedule successfully", schedule_dict)

    async def update(self, id: str, payload: UpdateScheduleRequest):
        try:
            oid = PydanticObjectId(id)
        except:
            raise HTTPException(status_code=404, detail="Invalid ID format")
        schedule = await ScheduleItem.get(oid)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        update_data = payload.model_dump(exclude_unset=True)
        await schedule.set(update_data)
        return success_response("Schedule updated successfully")

    async def delete(self, id: str):
        try:
            oid = PydanticObjectId(id)
        except:
            raise HTTPException(status_code=404, detail="Invalid ID format")
        schedule = await ScheduleItem.get(oid)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        await schedule.delete()
        return success_response("Schedule deleted successfully")

    async def create_event_google_calendar(
        self, schedule_id: str, user_id: str, events: List[GoogleCalendarEventRequest]
    ):
        user = await User.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        gc_info = getattr(user, "google_calendar", None)

        if not gc_info or not gc_info.access_token:
            raise HTTPException(status_code=400, detail="Không tìm thấy token Google Calendar.")

        schedule = await ScheduleItem.get(PydanticObjectId(schedule_id))
        if not schedule:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch trình")

        if schedule.is_schedule_completed:
            raise HTTPException(status_code=400, detail="Lịch trình đã được hoàn thành.")

        try:
            creds = Credentials(
                token=gc_info.access_token,
                refresh_token=gc_info.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("CALENDAR_CLIENT_ID"),
                client_secret=os.getenv("CALENDAR_CLIENT_SECRET"),
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            if creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
                user.google_calendar.access_token = creds.token
                await user.save()
        except Exception as e:
            print(f"Auth Error: {e}")
            raise HTTPException(status_code=401, detail="Token Google lỗi.")

        service = build("calendar", "v3", credentials=creds)
        results = []
        try:
            for event in events:
                event_body = event.model_dump()
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [{"method": "popup", "minutes": 0}],
                }
                event_result = (
                    service.events().insert(calendarId="primary", body=event_body).execute()
                )
                results.append(event_result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Google Calendar Error: {str(e)}")

        schedule.is_schedule_completed = True
        await schedule.save()

        try:
            start_date_str = (
                schedule.start_date.strftime("%d/%m/%Y") if schedule.start_date else "N/A"
            )
            end_date_str = schedule.end_date.strftime("%d/%m/%Y") if schedule.end_date else "N/A"
            user_name = getattr(user, "username", getattr(user, "full_name", user.email))

            email_payload = {
                "to": user.email,
                "name": user_name,
                "tripTitle": schedule.location,
                "startDate": start_date_str,
                "endDate": end_date_str,
                "totalEvents": len(results),
                "calendarLink": "https://calendar.google.com/calendar/r",
            }
            await send_google_add_schedule_email(email_payload)
        except:
            pass

        return success_response("Event created in Google Calendar successfully", results)


schedule_service = ScheduleService()
