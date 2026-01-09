from RAG.utils.rag_service import RAGService
from langchain_classic.retrievers import ParentDocumentRetriever
import json

async def retrieve_document_rag_wrapper(tool_input: str, retriever: ParentDocumentRetriever = None): 
    payload = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
    topics = payload.get("topic", [])
    locations = payload.get("location", [])
    query = payload.get("query", "")

    if isinstance(topics, str):
        topics = [topics]
        
    if isinstance(locations, str):
        locations = [locations]

    return await retrieve_document_rag(
        topics,
        locations,
        query,
        retriever,
        )

async def retrieve_document_rag(topics: list = [], locations: list = [], query: str = "", retriever: ParentDocumentRetriever = None):

    print(f"\n--- RAG Tool Input ---\nTopics: {topics}\nLocations: {locations}\nQuery: {query}\n--- End of RAG Tool Input ---\n")

    and_conditions = []

    if isinstance(topics, list) and len(topics) > 0:
        and_conditions.append({"Topic": {"$in": topics}})

    if isinstance(locations, list) and len(locations) > 0:
        and_conditions.append({"Location": {"$in": locations}})

    # Tạo filter dạng $and nếu có nhiều điều kiện
    if len(and_conditions) == 0:
        filter = {}
    elif len(and_conditions) == 1:
        filter = and_conditions[0]  # chỉ có 1 điều kiện → không cần $and
    else:
        filter = {"$and": and_conditions}

    # filter bây giờ có thể dùng cho retriever
    print(filter)
        
    retriever.search_kwargs["filter"] = filter

    print(f"\n--- RAG Tool Filter ---\n{filter}\n--- End of RAG Tool Filter ---\n")

    context_docs = await RAGService.retrieve_documents(retriever=retriever, query=query)
    page_contents = [doc.page_content for doc in context_docs]
    return page_contents

