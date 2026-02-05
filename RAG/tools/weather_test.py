import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import requests
from typing import Dict, Any
import json
from langchain_classic.tools import Tool
from models.weather_schema import WeatherInput
from langchain_classic.prompts import PromptTemplate
from langchain_classic.agents import create_react_agent, AgentExecutor
from core.llm import llm_plan

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class WeatherClient:
    def __init__(self):
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

    # def weather_tool_wrapper(tool_input: str) -> Dict[str, Any]:
    #     """Expects tool_input as JSON string."""
    #     payload = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
    #     city = payload.get("city")
    #     start_date = payload.get("start_date")
    #     end_date = payload.get("end_date")
    #     return weather_forecast(city=city, start_date=start_date, end_date=end_date)

    def get_coordinates(self, city: str) -> Dict[str, Any]:
        geo_url = "https://api.openweathermap.org/geo/1.0/direct"
        geo_res = requests.get(
            geo_url, params={"q": city, "limit": 1, "appid": self.OPEN_WEATHER_API_KEY}
        )
        geo_res.raise_for_status()
        geo = geo_res.json()
        if not geo:
            raise ValueError(f"Không tìm thấy tọa độ cho: {city}")
        return {"lat": geo[0]["lat"], "lon": geo[0]["lon"]}

    def normalize_weather(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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
            daily.append(
                {
                    "date": d.get("date"),
                    "minTempC": day.get("mintemp_c"),
                    "maxTempC": day.get("maxtemp_c"),
                    "conditionText": (day.get("condition") or {}).get("text"),
                    "chanceOfRain": day.get("daily_chance_of_rain"),
                }
            )

        return {
            "location": {"name": loc.get("name"), "country": loc.get("country")},
            "current": current,
            "daily": daily,
        }

    def weather_forecast(
        self, city: str, start_date: str = None, end_date: str = None, lang: str = "vi"
    ) -> Dict[str, Any]:
        today = date.today()

        if start_date:
            s = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            s = today

        if end_date:
            e = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            e = s + timedelta(days=2)

        if e < s:
            s, e = e, s

        if s < today:
            s = today

        days = (e - s).days + 1
        days = max(1, min(days, 14))

        coords = self.get_coordinates(city)
        lat, lon = coords["lat"], coords["lon"]

        weather_url = "https://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": self.WEATHER_API_KEY,
            "q": f"{lat},{lon}",
            "days": days,
            "lang": lang,
        }

        weather_res = requests.get(weather_url, params=params)
        weather_res.raise_for_status()
        raw = weather_res.json()

        normalized = self.normalize_weather(raw)

        valid_dates = [(s + timedelta(days=i)).isoformat() for i in range(days)]
        normalized["daily"] = [d for d in normalized["daily"] if d.get("date") in valid_dates]

        normalized["meta"] = {
            "query": {
                "city": city,
                "start_date": s.isoformat(),
                "end_date": e.isoformat(),
                "lang": lang,
            },
            "source": "weatherapi.com/forecast.json",
            "coordinates": {"lat": lat, "lon": lon},
            "units": "metric",
        }

        return normalized


def get_weather(data: WeatherInput):
    if isinstance(data, str):
        data = json.loads(data)

    city = data["city"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    weather_client = WeatherClient()
    weather_data = weather_client.weather_forecast(
        city=city, start_date=start_date, end_date=end_date, lang="vi"
    )

    return weather_data


get_weather_tool = Tool.from_function(
    func=get_weather,
    name="weather_forecast",
    description=(
        "Retrieve a 3–7 day weather forecast for a specific city and date range. "
        "Use this tool to get weather details relevant to a planned trip itinerary. "
        "Input must be a JSON object with the following fields: "
        "{ "
        '"city": "Name of the supported city (Ho Chi Minh, Da Nang,Hanoi or Bac Ninh)", '
        '"start_date": "Start date in YYYY-MM-DD", '
        '"end_date": "End date in YYYY-MM-DD" '
        "}. "
        "Output returns temperature, conditions, and other daily forecast details."
    ),
)

PROMPT = """
You are a Weather Agent that provides 3–7 day forecasts for trip planning.

You have access to these tools:
{tools}

Tool names: {tool_names}

RULES:
1. Date handling:
   - If the user explicitly mentions a time or date (e.g., "today", "tomorrow", "this weekend", or specific dates like "from Nov 3 to Nov 6"),
     always use that exact time range for the forecast.
   - If the user does not specify start_date and end_date:
       • Assume `start_date = {current_date}`
       • `end_date = start_date + 3 days`
   - Perform this reasoning inside Thought, not as an Action.

2. Tool usage:
   - Only use tools listed in [{tool_names}].
   - Action Input must always be valid JSON.
   - Never invent or call a non-existent tool.

3. Stop condition:
   - Once you receive an Observation that already contains weather data 
     (e.g., temperature, condition, humidity, or daily forecast),
     you MUST stop reasoning immediately.
   - Do NOT restate or re-analyze the question.
   - Do NOT call the same tool again for the same input.
   - Proceed directly to:
       Thought: I now know the final answer.
       Final Answer: <concise forecast summary>

4. Style:
   - Keep the final answer concise and factual.
   - No greetings, apologies, or extra explanations.

FORMAT:
Thought: Reason about what to do.
Action: Choose one of [{tool_names}]
Action Input: JSON for that tool
Observation: The tool result
... (repeat if needed)
Thought: I now know the final answer.
Final Answer: Short summary of the forecast.

BEGIN
Question: {input}
Thought: {agent_scratchpad}
"""


weather_prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad"],
    template=PROMPT,
)

agent = create_react_agent(
    llm=llm_plan(),
    tools=[get_weather_tool],
    prompt=weather_prompt.partial(current_date=datetime.now().date().isoformat()),
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[get_weather_tool],
    verbose=True,
    handle_parsing_errors=True,
    max_execution_time=30,
    max_iterations=5,
)

if __name__ == "__main__":
    query = "Thời tiết hồ chí minh hôm nay?"
    result = agent_executor.invoke({"input": query})
    print(result)
