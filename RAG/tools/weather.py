import requests
from typing import Dict, List, Any
from datetime import datetime, date
import os
from pathlib import Path
from dotenv import load_dotenv
import json

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def weather_tool_wrapper(tool_input: str) -> Dict[str, Any]:
    """Expects tool_input as JSON string."""
    payload = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
    city = payload["city"]
    start_date = payload["start_date"]
    end_date = payload["end_date"]
    return weather_forecast(city=city, start_date=start_date, end_date=end_date)



def get_coordinates(city: str) -> Dict[str, Any]:
    # 1) Geocode tên thành phố -> lat/lon
    geo_url = "https://api.openweathermap.org/geo/1.0/direct"
    geo_res = requests.get(geo_url, params={"q": city, "limit": 1, "appid": "6a47f87d4c6bcc356952f653697e4c93"})
    geo_res.raise_for_status()
    geo = geo_res.json()
    if not geo:
        raise ValueError(f"Không tìm thấy tọa độ cho: {city}")
    lat, lon = geo[0]["lat"], geo[0]["lon"]
    return {"lat": lat, "lon": lon}


def _normalize_weather(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa JSON từ WeatherAPI -> dạng gọn nhẹ, chỉ giữ thông tin cần thiết:
    {
      location: { name, country },
      current: { tempC, conditionText, humidity },
      daily: [{ date, minTempC, maxTempC, conditionText, chanceOfRain }]
    }
    """
    loc = payload.get("location", {}) or {}
    cur = payload.get("current", {}) or {}
    fcs = (payload.get("forecast", {}) or {}).get("forecastday", []) or []

    current = {
        "tempC": cur.get("temp_c"),
        "conditionText": (cur.get("condition") or {}).get("text"),
        "humidity": cur.get("humidity"),
    }

    daily = []
    for d in fcs:
        day = d.get("day", {}) or {}
        daily.append({
            "date": d.get("date"),
            "minTempC": day.get("mintemp_c"),
            "maxTempC": day.get("maxtemp_c"),
            "conditionText": (day.get("condition") or {}).get("text"),
            "chanceOfRain": day.get("daily_chance_of_rain"),
        })

    return {
        "location": {
            "name": loc.get("name"),
            "country": loc.get("country"),
        },
        "current": current,
        "daily": daily,
    }

def weather_forecast(city: str, start_date: str, end_date: str, lang: str = "vi") -> Dict[str, Any]:
    start_time = datetime.now()
    
    s = datetime.strptime(start_date, "%Y-%m-%d").date()
    e = datetime.strptime(end_date, "%Y-%m-%d").date()
    if e < s:
        s, e = e, s  # đảo ngược nếu nhập nhầm

    # Fix
    intended_duration_days = (e - s).days + 1

    # 2. Kiểm tra ngày bắt đầu
    today = date.today()
    if s < today:
        # Nếu ngày bắt đầu là quá khứ, hãy dùng ngày hôm nay
        s = today
        # Và tính lại ngày kết thúc dựa trên duration
        # (e.g., s = "2025-11-15" + (3 - 1) ngày = "2025-11-17")
        e = s + (e - s).__class__(days=intended_duration_days - 1) ### SỬA LỖI ###

    # 3. Tính số ngày cuối cùng và giới hạn (1-14 ngày)
    days = (e - s).days + 1
    if days < 1:
        days = 1
    if days > 14:
        days = 14
        # Cập nhật lại ngày kết thúc nếu vượt quá 14 ngày
        e = s + (e-s).__class__(days=13)

    # # WeatherAPI chỉ forecast từ hôm nay trở đi; nếu start_date < hôm nay -> dùng hôm nay
    # today = date.today()
    # if s < today:
    #     s = today
    # # số ngày cần lấy (1..14)
    # days = (e - s).days + 1
    # if days < 1:
    #     days = 1
    # if days > 14:
    #     days = 14

    # 1) Lấy toạ độ
    coords = get_coordinates(city=city)
    lat, lon = coords["lat"], coords["lon"]

    # 2) Gọi WeatherAPI forecast (không dùng dt cho range; dùng 'days')
    weather_url = "https://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": os.getenv("WEATHER_API_KEY"),
        "q": f"{lat},{lon}",
        "days": days,
        "lang": lang,
        # Có thể thêm: "aqi": "no", "alerts": "yes"
    }
    weather_res = requests.get(weather_url, params=params)
    weather_res.raise_for_status()
    raw = weather_res.json()

    # 3) Chuẩn hoá dữ liệu
    normalized = _normalize_weather(raw)

    # 4) (Tuỳ chọn) Cắt bớt daily theo đúng range s..e (vì WeatherAPI trả từ hôm nay)
    # Lọc theo yyyy-mm-dd
    want_dates = set((s + (e - s).__class__(days=i)).isoformat() for i in range(days))
    normalized["daily"] = [d for d in normalized["daily"] if d.get("date") in want_dates]

    # 5) Bổ sung meta cho frontend
    normalized["meta"] = {
        "query": {"city": city, "start_date": s.isoformat(), "end_date": e.isoformat(), "lang": lang},
        "source": "weatherapi.com/forecast.json",
        "coordinates": {"lat": lat, "lon": lon},
        "units": "metric"
    }
    return normalized

