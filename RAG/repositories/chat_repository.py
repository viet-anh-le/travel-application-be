from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from RAG.models.chat_schema import ChatMessage
from bson.objectid import ObjectId
from bson.errors import InvalidId

class ChatRepository:
    def __init__(self, db: AsyncIOMotorClient, user_id: str):
        self.collection = db["chat_sessions"]

        try:
            self.user_id = ObjectId(user_id)
        except InvalidId:
            raise ValueError(f"'{user_id}' không phải là một ObjectId hợp lệ.")


    async def save_message(self, session_id: str, message: ChatMessage):
        message_data = message.model_dump()
    
        await self.collection.update_one(
            {"session_id": session_id, "user_id": self.user_id},
            {
                "$push": {"messages": message_data},
                "$set": {"updated_at": datetime.now(), "user_id": self.user_id},
                "$setOnInsert": {"created_at": datetime.now()}
            },
            upsert=True
        )
        return message
        
    async def get_chat_history(self, session_id: str):

        if session_id == "default":
            return []
        
        if not self.user_id:
            return []

        try:
            session = await self.collection.find_one(
                {"session_id": session_id, 
                "user_id": self.user_id})

            if session and "messages" in session:
                # Lấy 5 phần tử cuối cùng
                return session["messages"][-5:]
            else:
                return []

        except Exception as e:
            return []


    
    def get_all_sessions(self):
        return list(self.collection.find({"user_id": self.user_id}))
    