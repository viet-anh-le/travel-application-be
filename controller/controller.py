import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorClient

from RAG.models.chat_schema import ChatMessage
from RAG.repositories.redis_chat_repository import RedisChatRepository
from RAG.repositories.schedule_repository import ScheduleRepository
from RAG.request.AskRequest import AskRequest
from RAG.response.AskResponse import AskResponse
from RAG.utils.rag_service import RAGService
from RAG.core.dependencies import (
    get_mongodb_instance,
    get_parent_document_retriever,
    get_chat_repository,
    get_schedule_repository,
)
from RAG.utils.agent_service import AgentService
from RAG.utils.callbacks import AgentStatusCallbackHandler
from RAG.repositories.chat_repository import ChatRepository
from RAG.utils.chat_history import build_chat_history_from_db
from langchain_classic.retrievers import ParentDocumentRetriever
from middleware.auth_jwt import get_current_user_payload_strict

router = APIRouter()


@router.post("/detect-topic")
async def detect_topic(payload: AskRequest):
    """
    Classify user message to detect if it's a travel planning request (topic=Plan).
    Returns: {"topic": "Plan" | "Other", "location": "..."}
    """
    message = payload.message
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message'")

    classify_result = await RAGService.classify_query(message)

    topic = classify_result.get("Topic") or None
    location = classify_result.get("Location") or None

    is_planning = topic and "Plan" in topic

    return {"topic": "Plan" if is_planning else "Other", "location": location, "raw_topic": topic}


@router.post("/create-schedule", response_model=AskResponse)
async def create_schedule(
    request: Request,
    payload: AskRequest,
    user_payload: dict = Depends(get_current_user_payload_strict),
    mongodb_instance: AsyncIOMotorClient = Depends(get_mongodb_instance),
    parent_document_retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
    schedule_repository: ScheduleRepository = Depends(get_schedule_repository),
):

    print(
        "\n---------------------Received Create Schedule Request---------------------\n" "Payload:",
        payload,
    )
    message = payload.message
    session_id = payload.session_id

    user_id = user_payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: User ID missing.")

    # Validate input
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message'")

    chat_repository = ChatRepository(mongodb_instance, user_id)
    past_messages = await chat_repository.get_chat_history(session_id=session_id)

    chat_history = build_chat_history_from_db(past_messages)

    print("\n---------------------Original question---------------------\n")
    print(message)
    standalone_question = None
    if len(chat_history) > 0:
        # Create standalone question from chat history
        standalone_res = await RAGService.build_standalone_question(message, chat_history)
        standalone_question = standalone_res.get("standalone_question", message)

        print("\n---------------------Standalone question---------------------\n")
        print(standalone_question)

    if standalone_question is None:
        classify_result = await RAGService.classify_query(message)
        standalone_question = message
    else:
        classify_result = await RAGService.classify_query_for_schedule(standalone_question)

    topic = classify_result.get("Topic") or None
    location = classify_result.get("Location") or None

    if location is None:
        await chat_repository.save_message(
            session_id=session_id, message=ChatMessage(content=message, role="human")
        )
        ai_message = chat_repository.save_message(
            session_id=session_id,
            message=ChatMessage(
                content="Vui lòng chọn một trong bốn địa điểm hiện được hỗ trợ: Hà Nội, TP.HCM, Đà Nẵng hoặc Bắc Ninh, để tôi có thể giúp bạn xây dựng lịch trình du lịch phù hợp.",
                role="ai",
            ),
        )

        return AskResponse(
            message=payload.message,
            answer="Vui lòng chọn một trong bốn địa điểm hiện được hỗ trợ: Hà Nội, TP.HCM, Đà Nẵng hoặc Bắc Ninh, để tôi có thể giúp bạn xây dựng lịch trình du lịch phù hợp.",
            timestamp=ai_message.timestamp,
        )

    if topic is None or "Plan" not in topic:
        await chat_repository.save_message(
            session_id=session_id, message=ChatMessage(content=message, role="human")
        )
        ai_message = await chat_repository.save_message(
            session_id=session_id,
            message=ChatMessage(
                content="Yêu cầu của bạn không liên quan đến việc lập kế hoạch du lịch. Vui lòng gửi yêu cầu khác.",
                role="ai",
            ),
        )

        return AskResponse(
            message=payload.message,
            answer="Có vẻ như yêu cầu của bạn chưa liên quan đến việc lập kế hoạch du lịch. Bạn vui lòng gửi lại yêu cầu khác để tôi có thể hỗ trợ chính xác hơn nhé!",
            timestamp=ai_message.timestamp,
        )
    response_queue = asyncio.Queue()
    callback_handler = AgentStatusCallbackHandler(response_queue)
    agent_service = AgentService(
        chat_repository=chat_repository, retriever=parent_document_retriever, user_id=user_id
    )

    async def run_agent_in_background():
        try:
            result = await agent_service.arun_agent(
                question=standalone_question, session_id=session_id, callbacks=[callback_handler]
            )

            await response_queue.put(
                {
                    "type": "answer",
                    "data": result.get("output") or result.get("answer"),
                    "trip_id": result.get("trip_id"),
                    "ai_message_for_history": result.get("ai_message_for_history"),
                }
            )
        except Exception as e:
            print(f"Agent Error: {e}")
            await response_queue.put({"type": "error", "data": str(e)})
        finally:
            await response_queue.put(None)

    asyncio.create_task(run_agent_in_background())

    async def response_generator():
        final_answer_data = None

        try:
            while True:
                token = await response_queue.get()
                if token is None:
                    break

                if token.get("type") == "error":
                    yield json.dumps(token)
                    break

                if token.get("type") == "answer":
                    final_answer_data = token
                    yield json.dumps(
                        {"type": "answer", "data": token["data"], "trip_id": token.get("trip_id")}
                    ) + "\n"

                elif token.get("type") == "thought":
                    yield json.dumps(token) + "\n"

        finally:
            if final_answer_data:
                print("Saving schedule chat to DB...")
                try:
                    trip_id = final_answer_data.get("trip_id")
                    if trip_id and await request.is_disconnected():
                        await run_in_threadpool(
                            schedule_repository.delete_schedule_by_trip_id, str(trip_id)
                        )
                    else:
                        ai_msg = (
                            final_answer_data.get("ai_message_for_history")
                            or final_answer_data["data"]
                        )
                        await chat_repository.save_message(
                            session_id=session_id,
                            message=ChatMessage(content=message, role="human"),
                        )
                        await chat_repository.save_message(
                            session_id=session_id,
                            message=ChatMessage(content=ai_msg, role="ai", trip_id=trip_id),
                        )
                except Exception as e:
                    print(f"Error saving chat history: {e}")

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")


@router.post("/ask", response_model=AskResponse)
async def ask(
    request: Request,
    payload: AskRequest,
    chat_repository: ChatRepository | RedisChatRepository = Depends(get_chat_repository),
    parent_document_retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
):
    print("\n---------------------Received Ask Request---------------------\n" "Payload:", payload)

    message = payload.message
    session_id = payload.session_id

    # Validate input
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message'")

    async def response_generator():
        yield json.dumps({"type": "thought", "data": "Đang đọc lịch sử trò chuyện..."}) + "\n"
        # Get all history messages from db
        past_messages = await chat_repository.get_chat_history(session_id=session_id)
        if len(past_messages) > 6:
            past_messages = past_messages[-6:]
        chat_history = build_chat_history_from_db(past_messages)

        yield json.dumps({"type": "thought", "data": "Đang phân tích ngữ cảnh..."}) + "\n"

        standalone_question = message
        if len(chat_history) > 0:
            res = await RAGService.build_standalone_question(message, chat_history)
            standalone_question = res.get("standalone_question", message)
        classify_result = await RAGService.classify_query(standalone_question)

        topics = classify_result.get("Topic") or []
        locations = classify_result.get("Location") or []

        and_conditions = []

        if isinstance(topics, list) and len(topics) > 0:
            and_conditions.append({"Topic": {"$in": topics}})

        if isinstance(locations, list) and len(locations) > 0:
            and_conditions.append({"Location": {"$in": locations}})

        if len(and_conditions) == 0:
            filter = {}
        elif len(and_conditions) == 1:
            filter = and_conditions[0]
        else:
            filter = {"$and": and_conditions}

        parent_document_retriever.search_kwargs["filter"] = filter
        full_ai_response = ""
        try:
            stream_iterator = RAGService.generate_response(
                parent_document_retriever,
                payload,
                standalone_question,
                chat_history,
                topics,
                locations,
            )
            async for chunk in stream_iterator:
                if await request.is_disconnected():
                    print("Client disconnected mid-stream")
                    break

                if chunk.get("type") == "context":
                    print("Context found:", len(chunk.get("data", [])))
                    continue

                if chunk.get("type") == "content":
                    content_data = chunk.get("data", "")
                    if not content_data:
                        continue
                    full_ai_response += content_data
                    yield json.dumps({"type": "content", "data": content_data}) + "\n"
            print("\n---------------------Stream finished, saving to DB---------------------\n")
            await chat_repository.save_message(
                session_id=session_id, message=ChatMessage(content=message, role="human")
            )
            if full_ai_response:
                await chat_repository.save_message(
                    session_id=session_id, message=ChatMessage(content=full_ai_response, role="ai")
                )
        except Exception as e:
            print(f"Streaming error: {e}")
            yield json.dumps({"type": "error", "data": f"Lỗi hệ thống: {str(e)}"}) + "\n"

    if await request.is_disconnected():
        print("Client disconnected after RAG generation, skip DB save")
        return Response(status_code=204)
    return StreamingResponse(response_generator(), media_type="application/x-ndjson")


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/health/db")
def check_database(request: Request):
    print("\n---------------------Checking Database Connection---------------------\n")
    try:
        db = request.app.state.db
        db.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
