from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

client = chromadb.PersistentClient(path="./RAG/chroma_db")

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
