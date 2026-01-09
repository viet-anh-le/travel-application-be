import os
import shutil
import io
import uuid
import pandas as pd
from typing import List
from langchain_core.documents import Document
from langchain_community.storage import MongoDBStore
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from fastapi import UploadFile
from pymongo.collection import Collection

class DataService:
    REQUIRED_EXCEL_COLUMNS = ['Name', 'Document', 'Location', 'Topic', 'Source']

    @staticmethod
    async def ingest_excel(
        file: UploadFile,
        file_id: str,
        retriever: ParentDocumentRetriever
    ) -> List[str]:
        try:
            content_file = await file.read()
            file_stream = io.BytesIO(content_file)
            df = pd.read_excel(file_stream).fillna("")
        except Exception as e:
            raise ValueError(f"Không thể đọc file Excel. Lỗi: {str(e)}")
        
        current_columns = df.columns.tolist()
        
        missing_columns = [col for col in DataService.REQUIRED_EXCEL_COLUMNS if col not in current_columns]
        
        if missing_columns:
            raise ValueError(
                f"File Excel không đúng mẫu quy định. "
                f"Thiếu các cột: {', '.join(missing_columns)}. "
                f"Các cột bắt buộc là: {', '.join(DataService.REQUIRED_EXCEL_COLUMNS)}"
            )

        documents = []

        file_id = str(file_id)

        df = df[DataService.REQUIRED_EXCEL_COLUMNS]

        for _, row in df.iterrows():
            content = str(row.get("Document", ""))
            if not content.strip():
                continue

            metadata = {col: str(row.get(col, "")) for col in DataService.REQUIRED_EXCEL_COLUMNS if col != "Document"}
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

            doc.metadata["file_id"] = file_id

        if documents:
            print(f"\n---------------------Ingesting {len(documents)} documents from uploaded Excel file---------------------\n")
            retriever.add_documents(documents)
            return file_id
        
        print(f"\n---------------------Ingested {len(documents)} documents from uploaded Excel file successfully---------------------\n")
        return []
    @staticmethod
    def ingest_unstructured_file(
        file: UploadFile,
        file_id: str,
        metadata: dict, 
        retriever: ParentDocumentRetriever
    ) -> List[str]:
        temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            documents = []

            file_id = str(file_id)

            if file.filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(temp_filename)
                documents = loader.load()
            elif file.filename.lower().endswith(".docx"):
                loader = Docx2txtLoader(temp_filename)
                documents = loader.load()
            elif file.filename.lower().endswith(".txt"):
                loader = TextLoader(temp_filename)
                documents = loader.load()
            else:
                raise ValueError(f"Unsupported file format: {file.filename}")

            if not documents:
                return []

            full_content = "\n\n".join([doc.page_content for doc in documents])
            
            final_metadata = metadata.copy()

            final_metadata["file_id"] = file_id
            
            new_doc = Document(page_content=full_content, metadata=final_metadata)

            retriever.add_documents([new_doc])
            return file_id

        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    @staticmethod
    def delete_document(
        file_id: str, 
        retriever: ParentDocumentRetriever
    ):
        print(f"--- Deleting Document ID: {file_id} ---")
        
        try:
            if hasattr(retriever.docstore, "collection"):
                result = retriever.docstore.collection.delete_many(
                    {"value.metadata.file_id": file_id}
                )
                print(retriever.docstore.collection)
                print(f"Deleted {result.deleted_count} parent docs from MongoDB")
        except Exception as e:
            print(f"Warning: Failed to delete from MongoDB (ID might not exist): {e}")

        # Xóa trong Chroma (Vectorstore)
        try:
            # Dùng filter file_id để xóa tất cả chunks con
            retriever.vectorstore.delete(where={"file_id": file_id})
            print("Successfully deleted from Chroma Vectorstore")
            return True
        except Exception as e:
            print(f"Error deleting from Chroma: {e}")
        return False
    @staticmethod
    def ingest_data(documents: List[Document], store: MongoDBStore, vector_store):
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""])
        
        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        parent_document_retriever = ParentDocumentRetriever(
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
            docstore=store,
            vectorstore=vector_store
        )

        print(f"\n---------------------Ingesting {len(documents)} documents into MongoDB store and Chroma vector store---------------------\n")
        parent_document_retriever.add_documents(documents)
        print(f"\n---------------------Ingested {len(documents)} documents successfully---------------------\n")

    @staticmethod
    def load_raw_data(
        filepath: str,
        document_column: str = "Document",
        metadata_columns: List[str] = ["Name", "Location", "Topic", "Source"]
    ) -> List[Document]:
        df = pd.read_excel(filepath).fillna("")

        documents = []

        for index, row in df.iterrows():
            main_document_text = str(row.get(document_column, ""))

            metadata = {col: str(row.get(col, "")) for col in metadata_columns}
            
            doc = Document(page_content=main_document_text, metadata=metadata)

            documents.append(doc)

        print(f"\n---------------------Transformed {len(df)} rows into {len(documents)} document chunks---------------------\n")
        return documents
    
    @staticmethod
    def get_all_files(retriever: ParentDocumentRetriever) -> List[dict]:
        """
        Lấy danh sách các file duy nhất từ MongoDB bằng cách group theo file_id.
        """
        try:
            if not hasattr(retriever.docstore, "collection"):
                 raise ValueError("Docstore is not a MongoDBStore or missing collection access.")
            
            collection: Collection = retriever.docstore.collection

            pipeline = [
                {"$match": {"value.metadata.file_id": {"$exists": True}}},
                
                {"$group": {
                    "_id": "$value.metadata.file_id",
                    "name": {"$first": "$value.metadata.Name"},
                    "topic": {"$first": "$value.metadata.Topic"},
                    "location": {"$first": "$value.metadata.Location"},
                    "source": {"$first": "$value.metadata.Source"},
                    "preview": {"$first": "$value.page_content"} 
                }},
                
                {"$project": {
                    "_id": 0,
                    "file_id": "$_id",
                    "name": {"$ifNull": ["$name", "Unknown"]},
                    "topic": {"$ifNull": ["$topic", "General"]},
                    "location": {"$ifNull": ["$location", "Unknown"]},
                    "source": {"$ifNull": ["$source", "Unknown"]},
                    "preview": {"$substrCP": ["$preview", 0, 100]} 
                }}
            ]

            results = list(collection.aggregate(pipeline))
            return results

        except Exception as e:
            print(f"Error retrieving files from MongoDB: {str(e)}")
            return []