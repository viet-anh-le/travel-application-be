import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ParentDocumentRetriever
from langchain_classic.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from RAG.utils.split_data import load_content

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant="bc825549-1d01-4610-b4b4-43f7cb23f360",
    database="Travel",
)


def create_vectordb(chunks):
    embeddings = HuggingFaceEmbeddings(
        model_name="google/embeddinggemma-300m", model_kwargs={"device": "cpu"}
    )

    collection_name = "Van_mieu_Quoc_Tu_Giam"

    documents = [doc.page_content.lower() for doc in chunks]
    metadatas = [doc.metadata for doc in chunks]
    ids = [str(i) for (i, _) in enumerate(chunks)]

    existing_collections = [col.name for col in client.list_collections()]
    if collection_name in existing_collections:
        # client.delete_collection(name=collection_name)
        print(f"{collection_name}")

    collection = client.get_or_create_collection(
        name=collection_name,
        configuration={
            "hnsw": {"space": "cosine"},
            "embedding_function": SentenceTransformerEmbeddingFunction(
                model_name="google/embeddinggemma-300m"
            ),
        },
    )

    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    vectordb = Chroma(
        client=client,
        collection_name="Van_mieu_Quoc_Tu_Giam",
        embedding_function=embeddings,
    )
    return vectordb


def create_ensemble_retriever(vectordb, query):
    vectordb_retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    top_docs = vectordb.similarity_search_with_score(query, k=100)
    top_docs = [doc for doc, score in top_docs]

    retriever_bm25 = BM25Retriever.from_documents(top_docs)
    retriever_bm25.k = 5

    ensemble_retriever = EnsembleRetriever(
        retrievers=[vectordb_retriever, retriever_bm25], weights=[0.7, 0.3]
    )
    return ensemble_retriever


def create_parent_retriever(filepath):
    embeddings = HuggingFaceEmbeddings(
        model_name="google/embeddinggemma-300m", model_kwargs={"device": "cpu"}
    )
    docs = load_content(filepath)
    vectordb = Chroma(client=client, collection_name="split_parents", embedding_function=embeddings)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=20)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=20)
    store = InMemoryStore()
    retriever = ParentDocumentRetriever(
        vectorstore=vectordb,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    retriever.add_documents(docs)
    return retriever
