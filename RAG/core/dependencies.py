from http.client import HTTPException
from fastapi import Request, Header
from fastapi.params import Depends
from redis import Redis
from RAG.core.security import decode_access_token
from middleware.auth_jwt import get_user_payload_optional
from RAG.repositories.chat_repository import ChatRepository
from RAG.repositories.chroma_repository import ChromaRepository
from langchain_community.document_compressors import FlashrankRerank
from langchain_community.storage import MongoDBStore
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_classic.retrievers import ParentDocumentRetriever
from RAG.config.redis_cache import get_redis_instance
from RAG.repositories.redis_chat_repository import RedisChatRepository

def get_chroma_repository(request: Request):
    if not hasattr(request.app.state, 'chroma_repository'):
        raise RuntimeError("Chroma repository not initialized in app state.")
        
    return request.app.state.chroma_repository

def get_flashrank_compressor(request: Request) -> FlashrankRerank:
    if not hasattr(request.app.state, 'flashrank_compressor'):
        raise RuntimeError("FlashRank compressor not initialized in app state.")
        
    return request.app.state.flashrank_compressor

def get_mongodb_instance(request: Request) -> AsyncIOMotorClient:
    if not hasattr(request.app.state, 'db'):
        raise RuntimeError("MongoDB instance not initialized in app state.")
        
    return request.app.state.db

def get_docstore(request: Request) -> MongoDBStore:
    if not hasattr(request.app.state, 'docstore'):
        raise RuntimeError("MongoDBStore not initialized in app state.")

    return request.app.state.docstore

def get_parent_document_retriever(request: Request) -> ParentDocumentRetriever:
    if not hasattr(request.app.state, 'parent_document_retriever'):
        raise RuntimeError("ParentDocumentRetriever not initialized in app state.")

    return request.app.state.parent_document_retriever

def get_reranker_service(request: Request):
    if not hasattr(request.app.state, 'reranker_service'):
        raise RuntimeError("RerankerService not initialized in app state.")

    return request.app.state.reranker_service

async def get_redis_instance(request: Request):
    try:
        return request.app.state.redis_instance
    except AttributeError:
        # Dự phòng nếu redis chưa được khởi tạo
        redis_conn = await get_redis_instance()
        request.app.state.redis_instance = redis_conn
        return redis_conn

async def get_chat_repository(
    # Các dependency cơ sở
    mongodb_instance: AsyncIOMotorClient = Depends(get_mongodb_instance),
    redis_instance: Redis = Depends(get_redis_instance),
    # Dependency mới: Lấy payload người dùng
    user_payload: dict | None = Depends(get_user_payload_optional)
):
    """
    Quyết định cung cấp repository nào (Mongo/Redis)
    dựa trên việc JWT có hợp lệ hay không.
    """
    # Nếu user_payload không phải là None (tức là JWT hợp lệ)
    if user_payload:
        user_id = user_payload.get("id")

        if not user_id:
            raise HTTPException(401, "Invalid token: User ID missing.")

        print(f"\n---------------------Using MongoChatRepository (User: {user_id})---------------------\n")
        # Trả về repository dùng MongoDB
        return ChatRepository(mongodb_instance, user_id)
    
    # Nếu user_payload là None (khách hoặc token không hợp lệ)
    print("\n---------------------Using RedisChatRepository (Guest User)---------------------\n")
    # Trả về repository dùng Redis
    return RedisChatRepository(redis_instance)

def get_schedule_repository(request: Request):
    if not hasattr(request.app.state, 'schedule_repository'):
        raise RuntimeError("Schedule repository not initialized in app state.")
        
    return request.app.state.schedule_repository
