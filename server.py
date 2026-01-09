import sys
import os
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import numpy as np
from openwakeword.model import Model
import uvicorn
import argparse

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers import ParentDocumentRetriever

from RAG.config.mongodb import get_database, get_docstore, init_db, get_database_schedule
from RAG.config.chroma_vector_store import ChromaConfig
from RAG.config.redis_cache import redis_client
from RAG.repositories.chroma_repository import ChromaRepository
from RAG.repositories.schedule_repository import ScheduleRepository
from controller import controller, admin_controller, auth_controller,\
city_controller, place_controller, food_controller, festival_controller, accommodation_controller, schedule_controller

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
load_dotenv()
rag_path = os.path.join(os.path.dirname(__file__), "RAG")
if rag_path not in sys.path:
    sys.path.append(rag_path)

from STT.utils import stt_transcribe
# from RAG.run_rag import run_rag

@asynccontextmanager
async def life_span(app: FastAPI):
    try:
        # Initalize MongoDB connection
        await init_db() 
        print("\n--------------Connected to MongoDB (Project3) for Auth!-------------\n")
        db = await get_database()
        app.state.db = db
        print('\n---------------------Connected to MongoDB database---------------------\n', db.name)
        
        # Initialize schedule repository
        db_schedule = await get_database_schedule()
        schedule_repo = ScheduleRepository(db_schedule)
        app.state.schedule_repository = schedule_repo
        print('\n---------------------Initialized Schedule repository---------------------\n')
        
        # Initialize vector store
        vector_store = ChromaConfig.get_vector_store()

        app.state.chroma_repository = ChromaRepository(vector_store=vector_store)
        print('\n---------------------Initialized Chroma repository with vector store---------------------\n')

        # Initialize Docstore mongodb
        docstore = get_docstore()
        app.state.docstore = docstore
        print('\n---------------------Initialized MongoDB docstore---------------------\n')

        # Initialize ParentDocumentRetriever
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""])
        
        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        app.state.parent_document_retriever = ParentDocumentRetriever(docstore=docstore,
                                                                    child_splitter=child_splitter, 
                                                                    parent_splitter=parent_splitter,
                                                                    vectorstore=vector_store,
                                                                    search_kwargs={"k":15, "filter":{} })
        print('\n---------------------Initialized ParentDocumentRetriever---------------------\n')

        # Initialize redis cache
        await redis_client.ping()
        app.state.redis_instance = redis_client
        print('\n---------------------Initialized Redis cache instance---------------------\n')

    except Exception as e:
        raise RuntimeError(f"Failed to create vector_store/Chroma repository/Flashrank compressor/Database connection at start up: {e}")

    yield

    # Shutdown
    print("\n---------------------Shutting down FastAPI application---------------------\n")
    app.state.chroma_repository = None
    if hasattr(app.state, "db"):
        app.state.db.client.close()
        print("MongoDB connection closed")

    if hasattr(app.state, "redis_instance"):
        app.state.redis_instance.close()
        print("Redis connection closed")

app = FastAPI(lifespan=life_span)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sessions_texts = {}

parser=argparse.ArgumentParser()
parser.add_argument(
    "--chunk_size",
    help="How much audio (in number of samples) to predict on at once",
    type=int,
    default=1280,
    required=False
)
parser.add_argument(
    "--model_path",
    help="The path of a specific model to load",
    type=str,
    default="",
    required=False
)
parser.add_argument(
    "--inference_framework",
    help="The inference framework to use (either 'onnx' or 'tflite'",
    type=str,
    default='tflite',
    required=False
)

args=parser.parse_args()

# Load pre-trained openwakeword models
if args.model_path != "":
    owwModel = Model(wakeword_models=[args.model_path], inference_framework=args.inference_framework)
else:
    owwModel = Model(inference_framework=args.inference_framework)
    
n_models = len(owwModel.models.keys())

@app.websocket("/ws/detect")
async def detect(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_bytes()
        audio = np.frombuffer(data, dtype=np.int16)

        owwModel.predict(audio)

        result = {}
        for mdl in owwModel.prediction_buffer:
            score = owwModel.prediction_buffer[mdl][-1]
            result[mdl] = float(score)
            
        # print(f"===========result = {result}=================")

        await ws.send_json(result)

@app.post("/stt")
async def speech_recognize(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = stt_transcribe(audio_bytes)
    text = text.lower()
    print(text)
    return {"text": text}
        
app.include_router(controller.router)
app.include_router(admin_controller.router)
app.include_router(auth_controller.router)
app.include_router(city_controller.router)
app.include_router(place_controller.router)
app.include_router(food_controller.router)
app.include_router(festival_controller.router)
app.include_router(accommodation_controller.router)
app.include_router(schedule_controller.router)

# uvicorn.run(app, host="0.0.0.0", port=8000, log_level='warning')
uvicorn.run(app, host="0.0.0.0", port=8000)