import os
from dotenv import load_dotenv
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_community.storage import MongoDBStore
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import all_models

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

async def get_database() -> AsyncIOMotorClient:
    CONNECTION_STRING = os.getenv("MONGO_URL")
    client = AsyncIOMotorClient(CONNECTION_STRING)
    return client["project3"]

def get_docstore() -> MongoDBStore:
    CONNECTION_STRING = os.getenv("MONGO_URL")
    docstore = MongoDBStore(
        connection_string=CONNECTION_STRING,
        db_name="project3",
        collection_name="travel-tourism"
    )
    return docstore

async def get_database_schedule() -> AsyncIOMotorClient:
    CONNECTION_STRING = os.getenv("MONGO_URL")
    client = AsyncIOMotorClient(CONNECTION_STRING)
    return client["project3"]

async def init_db():
    CONNECTION_STRING = os.getenv("MONGO_URL")
    client = AsyncIOMotorClient(CONNECTION_STRING)
    database = client["project3"]
    await init_beanie(
        database=database, 
        document_models=all_models
    )
