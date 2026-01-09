from langchain_classic.tools import Tool
from RAG.tools.weather import weather_tool_wrapper
from RAG.tools.summary import summarize_text
from RAG.tools.schedule import schedule_trip

weather_tool = Tool.from_function(
    func=weather_tool_wrapper,
    name="weather_forecast",
    description=(
            "Retrieve a 3–7 day weather forecast for a specific city and date range. "
            "Use this tool to get weather details relevant to a planned trip itinerary. "
            "Input must be a JSON object with the following fields: "
            "{ "
            '"city": "Name of the supported city (Ho Chi Minh, Da Nang, or Hanoi)", '
            '"start_date": "Start date in YYYY-MM-DD", '
            '"end_date": "End date in YYYY-MM-DD" '
            "}. "
            "Output returns temperature, conditions, and other daily forecast details."
        )
)

summarization_tool = Tool.from_function(
    func=summarize_text,
    name="summarization_tool",
    description = (
        "Summarize and synthesize all collected trip information — including food, accommodation, "
        "attractions, and weather — into one coherent Vietnamese travel itinerary. "
        "Input: a single long text containing raw travel details gathered from previous tools. "
        "Task: distill this information into a concise, natural day-by-day trip summary written in Markdown. "
        "The tone should resemble a friendly, knowledgeable local tour guide. "
        "Do not fabricate or add new information beyond what is provided."
    )
)

schedule_tool = Tool.from_function(
    func=schedule_trip,
    name="schedule_tool",
    description=(
        "Create a new travel schedule and save it to MongoDB. "
        "Input must be a JSON object containing details such as user_id, trip_id, location, "
        "start_date, end_date, itinerary, weather_summary, and accommodation."
    )
)

TOOLS = [weather_tool, summarization_tool, schedule_tool]