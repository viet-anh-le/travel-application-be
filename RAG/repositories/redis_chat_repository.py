import json
from redis import Redis
from RAG.models.chat_schema import ChatMessage
from typing import List

class RedisChatRepository:
    def __init__(self, db: Redis, ttl_seconds: int = 3600): # Mặc định 1 giờ
        self.db = db
        self.ttl = ttl_seconds

    def _get_key(self, session_id: str) -> str:
        """Create Redis key for a given session ID."""
        return f"chat_session:{session_id}"

    async def save_message(self, session_id: str, message: ChatMessage):
        key = self._get_key(session_id)
        
        # Chuyển Pydantic model thành JSON string để lưu vào Redis
        message_json = message.model_dump_json()
        
        await self.db.rpush(key, message_json)
        
        # Reset TTL for the session
        await self.db.expire(key, self.ttl)

        return message

    async def get_chat_history(self, session_id: str) -> List[dict]:
        """
        Lấy lịch sử chat từ Redis List.
        Chỉ lấy 5 tin nhắn cuối cùng để khớp với logic của bản Mongo.
        """
        # Giữ nguyên logic đặc biệt cho "default" session
        if session_id == "default":
            return []

        key = self._get_key(session_id)

        try:
            # Lấy 5 phần tử cuối cùng từ list
            # LRANGE key -5 -1 (lấy từ vị trí thứ 5 từ cuối đến vị trí cuối cùng)
            history_json_list = await self.db.lrange(key, -5, -1)
            
            history = []
            for msg_json in history_json_list:
                try:
                    history.append(json.loads(msg_json))
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode chat message from Redis: {msg_json}")
            
            return history

        except Exception as e:
            print(f"Error getting chat history from Redis: {e}")
            return []