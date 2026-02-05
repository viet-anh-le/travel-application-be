import json
import re
from langchain_classic.agents import create_react_agent, AgentExecutor
from RAG.repositories.chat_repository import ChatRepository
from langchain_classic.retrievers import ParentDocumentRetriever
from RAG.tools.index import TOOLS
from RAG.core.llm import llm_plan
from RAG.config.prompt import get_react_prompt

from bson.objectid import ObjectId
from langchain_classic.tools import Tool
from RAG.tools.rag import retrieve_document_rag_wrapper
from RAG.tools.schedule import schedule_trip


class AgentService:
    def __init__(
        self, retriever: ParentDocumentRetriever, chat_repository: ChatRepository, user_id: str
    ):
        self.llm = llm_plan()
        self.chat_repository = chat_repository
        self.prompt = get_react_prompt()
        self.retriever = retriever
        self.user_id = user_id

        async def _rag_wrapper(tool_input: str):
            return await retrieve_document_rag_wrapper(tool_input, retriever=self.retriever)

        def _sync_rag_placeholder(tool_input: str):
            raise NotImplementedError("Tool này chỉ hỗ trợ chạy Async (ainvoke).")

        rag_tool = Tool.from_function(
            name="retrieve_document_rag",
            func=_sync_rag_placeholder,
            coroutine=_rag_wrapper,
            description=(
                "Retrieve detailed travel information from the RAG knowledge base for a given topic "
                "in one of the supported cities (Thành phố Hồ Chí Minh, Đà Nẵng, Bắc Ninh or Hà Nội). "
                "Use this tool to collect accurate local data about food, accommodations "
                "before generating the trip itinerary. "
                "Input must be a JSON object in the following format: "
                "{ "
                '"topic": A list containing exactly ONE category from: ["Food", "Accommodation", "Attraction", "Festival", "Transport"]. Example: ["Food"], '
                '"location": [Thành phố Hồ Chí Minh] | [Hà Nội] | [Đà Nẵng] | [Bắc Ninh], '
                '"query": "Short, focused question combining topic and location" '
                "}. "
                "Output returns relevant travel content and metadata for that topic."
            ),
        )

        def _sync_schedule_placeholder(trip_details_str: str):
            raise NotImplementedError("Schedule tool chỉ hỗ trợ chạy Async (ainvoke).")

        wrapped_schedule_tool = Tool.from_function(
            func=_sync_schedule_placeholder,
            coroutine=self.schedule_trip_wrapper,
            name="schedule_tool",
            description=(
                "Create a new travel schedule and save it to MongoDB. "
                "Input must be a JSON object containing details such as location, "
                "start_date, end_date, itinerary, weather_summary, and accommodation, tips."
                "The user_id will be added automatically by the system."
            ),
        )

        original_tools = TOOLS

        final_tools = [tool for tool in original_tools if tool.name != "schedule_tool"]

        final_tools.extend([rag_tool, wrapped_schedule_tool])

        self.TOOLS = final_tools

        agent = create_react_agent(llm=self.llm, tools=self.TOOLS, prompt=self.prompt)
        self.executor = AgentExecutor(
            agent=agent, tools=self.TOOLS, verbose=True, handle_parsing_errors=True
        )

    async def arun_agent(self, session_id: str, question: str, callbacks=None):
        result = await self.executor.ainvoke({"input": question}, config={"callbacks": callbacks})

        raw_output = result.get("output")

        print(f"\n--- Raw output from agent ---\n{raw_output}\n--- End of raw output ---\n")

        decoded_answer = None
        ai_message_for_history = ""
        json_string_to_parse = None

        match = re.search(r"```json\s*(\{.*\})\s*```", raw_output, re.DOTALL)

        # Ưu tiên 1: Dùng regex để tìm khối JSON trong markdown ```json ... ```
        if match:
            # Nếu tìm thấy, lấy nội dung JSON từ group 1
            json_string_to_parse = match.group(1)
            print(f"\n--- Đã trích xuất JSON bằng Regex (Markdown) ---\n")
        else:
            # Ưu tiên 2: Dùng find/rfind làm phương án dự phòng (cho JSON sạch)
            try:
                start_index = raw_output.find("{")
                end_index = raw_output.rfind("}")

                if start_index != -1 and end_index != -1 and end_index > start_index:
                    json_string_to_parse = raw_output[start_index : end_index + 1]
                else:
                    json_string_to_parse = raw_output
                print(f"\n--- Đã trích xuất JSON bằng find/rfind ---\n")
            except Exception as e:
                json_string_to_parse = raw_output

        trip_id = None

        try:
            decoded_answer = json.loads(json_string_to_parse)

            print(f"\n--- Decoded answer ---\n{decoded_answer}\n--- End of decoded answer ---\n")

            if isinstance(decoded_answer, dict):
                ai_message_for_history = decoded_answer.get("message", raw_output)
                ai_data = decoded_answer.get("data", None)
                trip_id = ai_data.get("trip_id", None) if ai_data else None
            else:
                ai_message_for_history = raw_output
                decoded_answer = raw_output

        except (json.JSONDecodeError, TypeError):
            ai_message_for_history = raw_output  # Dùng chuỗi thô (bị cắt) để lưu
            decoded_answer = raw_output

        return {
            "answer": decoded_answer,
            "ai_message_for_history": ai_message_for_history,
            "trip_id": trip_id,
        }

    async def schedule_trip_wrapper(self, trip_details_str: str):
        print(f"\n--- Wrapping schedule_tool for user: {self.user_id} ---\n")
        try:
            # 1. Parse JSON mà LLM cung cấp
            trip_details = json.loads(trip_details_str)

            # 2. Tiêm user_id (đã lưu trong self)
            trip_details["user_id"] = self.user_id

            generated_trip_id = ObjectId()
            trip_details["trip_id"] = generated_trip_id

            await schedule_trip(trip_details)

            return trip_details

        except json.JSONDecodeError as e:
            return f"Lỗi: JSON không hợp lệ. {e}"
        except Exception as e:
            return f"Lỗi khi lưu lịch trình: {e}"
