import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Any
from python_server.RAG.utils.rag_service import RAGService
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.storage import MongoDBStore
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb 
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_chroma import Chroma
from RAG.utils.get_llm import get_llm

client = chromadb.PersistentClient(path="./chroma_db")

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class RAGEvaluation:
    CONNECTION_STRING = os.getenv("MONGO_URL")

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    def __init__(self):
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
        self.docstore = MongoDBStore(
            connection_string=os.getenv("MONGO_URL"),
            db_name="project3",
            collection_name="travel-tourism"
        )
        # self.llm_rag_eval_faithfulness = llm_evaluate_faithfulness()
        # self.llm_rag_eval_relevance = llm_evaluate_relevance()
        # self.llm_rag_eval_precision = llm_evaluate_precision()
        # self.llm_rag_eval_recall = llm_evaluate_recall()
        self.parent_document_retriever = ParentDocumentRetriever(
            docstore=self.docstore,
            child_splitter=self.child_splitter,
            vectorstore=vector_store,
            search_kwargs={"k":15, "filter":{}}
        )

    # Implement RAG response generation for evaluation
    def generate_response(self, retriever, question: str, topics, locations) -> str:
        llm = get_llm()

        system = """### Role and Goal
            You are an AI assistant specializing in tourism. Your persona is friendly, helpful, and **extremely accurate**.
            Your task is to answer user questions, but you operate under one ABSOLUTE constraint: You MUST ONLY use the information provided to you.

            ### The Golden Rules (MOST IMPORTANT)
            1.  **Strict Faithfulness:** Your answer MUST be **ENTIRELY** derived from the provided 'Context'.
            2.  **No External Knowledge:** You are STRICTLY PROHIBITED from using any external knowledge (your pre-trained knowledge) to answer. If the information is not in the 'Context', you CANNOT say it.
            3.  **Natural Phrasing (No Meta-Talk):**
            * You must sound like a natural, human expert. 
            * **DO NOT** talk about yourself as an AI or mention your data sources. 
            * **AVOID ALL** phrases like: "in the documents I received," "based on the context," "in the provided information," "trong các tài liệu," "dựa trên ngữ cảnh," or "thông tin tôi nhận được."
            * Just state the information directly.
            4.  **Handling **Partial** Information (Best-Effort Rule):**
            * Your main goal is to be helpful.
            * If the user asks for a specific thing (e.g., "top 50 dishes", "Places to stay in somewhere near somewhere", "Places to visit near somewhere"), but the 'Context' provides **fewer items** or **items in context which is not near by mentioned places**, you **MUST** suggest **some the relevant items you found in the 'Context'**.
            * If this is a follow-up question (e.g., user asks for 70 after you just gave 50), simply state naturally that you don't have additional items.
            * **Example of a good response (natural):** "Hiện tại tôi chỉ có danh sách 50 món ăn này thôi." or "Danh sách của tôi có 50 món, tôi không tìm thấy món nào khác."
            * **Example of a bad response (robot):** "Trong tài liệu tôi chỉ tìm thấy 50 món."
            5.  **Handling **Completely** Missing Information (The "I don't know" rule):**
            * This rule ONLY applies if the 'Context' is **completely empty** OR **contains no relevant information AT ALL** to the 'Question'.
            * In this specific case, you **MUST** respond with this exact Vietnamese phrase: "Hiện tại tôi không thể trả lời câu hỏi của bạn vì tôi thiếu thông tin về dữ liệu đó". Do not add any other explanation.
            6.  **Handling Conversation History:**
                * Use the 'Conversation History' to understand follow-up questions (e.g., "what else?", "besides those...").
                * When answering a follow-up, **AVOID REPEATING** information already present in the 'Conversation History'. Prioritize NEW information found in the 'Context'.
            7.  **Handling Off-topic/Greeting:** If the 'Question' is a greeting or unrelated to tourism, respond politely, be friendly, and steer the conversation back to tourism (e.g., "Hello, how can I help you with your travel plans today?", "I can't help with that, but I can assist you with travel information.").
            8. No Post-amble: Do not add any summary sentences at the end explaining where the information came from. Just provide the direct answer.
            9.  **Language:** You must always answer in Vietnamese.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("user", """'Ngữ cảnh' để bạn tham khảo.
                <Ngữ cảnh>
                {context}
                </Ngữ cảnh>

                Hãy trả lời 'Câu hỏi' dưới đây dựa trên các quy tắc đã đề ra.
                Câu hỏi: {question}""")
        ])

        rag_chain = prompt | llm | StrOutputParser()

        if( 'Off_topic' in topics ):
            prompt_input = {
                "context": "",
                "question": question
            }
            
            response = rag_chain.invoke(prompt_input)

            return response

        context_docs = RAGService.retrieve_documents(retriever, question)

        formatted_contexts = []
        for doc in context_docs:
            name = doc.metadata.get('Name', 'Không rõ')
            
            context_str = f"Tên tài liệu: {name}\nNội dung: {doc.page_content}"
            formatted_contexts.append(context_str)

        prompt_input = {
            "context": "\n\n".join(formatted_contexts),
            "question": question
        }

        response = rag_chain.invoke(prompt_input)
        # response = ""

        return response, context_docs
