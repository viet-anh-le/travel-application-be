import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant='bc825549-1d01-4610-b4b4-43f7cb23f360',
    database='Travel'
)
class ChromaConfig:
    @staticmethod
    def get_vector_store():
        print(f"\n---------------------Connecting to Chroma index'---------------------\n")
        embeddings = HuggingFaceEmbeddings(
            model_name="google/embeddinggemma-300m",
            model_kwargs={"device": "cpu"} 
        )
        collection_name = "tourism_rag"
        collection = client.get_or_create_collection(
            name=collection_name,
            configuration={
                "hnsw": {"space": "cosine"},
                "embedding_function": SentenceTransformerEmbeddingFunction(model_name="google/embeddinggemma-300m")
            }
        )
        vector_store = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )
        return vector_store
