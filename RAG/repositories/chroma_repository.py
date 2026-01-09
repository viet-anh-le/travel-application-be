from langchain_core.documents import Document
from typing import List
import os

class ChromaRepository:
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.default_k = 5

        print(f"\n---------------------ChromaRepository initialized with default_k={self.default_k}---------------------\n")

    def get_retriever(self, k: int = None, filter: dict = None):
        k = k or self.default_k

        filter = filter or {}
        print(f"\n---------------------Creating retriever with top {k} documents---------------------\n")
        retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k, "filter": filter})
        print(f"\n---------------------Retriever created with top {k} documents---------------------\n")
        return retriever

    def import_data(self, chunks: List[Document]):
        try:
            print(f"\n---------------------Importing {len(chunks)} chunks to Chroma index---------------------\n")
            start_time_import = os.times()
            self.vector_store.add_documents(documents=chunks)
            end_time_import = os.times()
            print("\n---------------------Data import completed in", end_time_import.user - start_time_import.user, "seconds---------------------\n")
            
        except Exception as e:
            print(f"\n---------------------An error occurred while importing data to Chroma: {e}---------------------\n")

    