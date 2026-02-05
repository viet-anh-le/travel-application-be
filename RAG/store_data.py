import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_chroma import Chroma
from langchain_community.storage import MongoDBStore
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from utils.data_service import DataService
from langchain_huggingface import HuggingFaceEmbeddings

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant="bc825549-1d01-4610-b4b4-43f7cb23f360",
    database="Travel",
)


def main():
    docstore = MongoDBStore(
        connection_string=os.getenv("MONGO_URL"),
        db_name="project3",
        collection_name="travel-tourism",
    )
    # Create vectorstore
    embeddings = HuggingFaceEmbeddings(
        model_name="google/embeddinggemma-300m", model_kwargs={"device": "cpu"}
    )
    collection_name = "tourism_rag"
    collection = client.get_or_create_collection(
        name=collection_name,
        configuration={
            "hnsw": {"space": "cosine"},
            "embedding_function": SentenceTransformerEmbeddingFunction(
                model_name="google/embeddinggemma-300m"
            ),
        },
    )
    vector_store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    script_path = os.path.abspath(__file__)

    script_dir = os.path.dirname(script_path)

    file_path = os.path.join(script_dir, "data_tourism_DaNang.xlsx")
    documents = DataService.load_raw_data(filepath=file_path)
    print(f"\n---------------------Loaded {len(documents)} raw documents---------------------\n")

    DataService.ingest_data(documents, docstore, vector_store)


if __name__ == "__main__":
    main()
    # pass
