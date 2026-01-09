from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_content(filepath):
    loader = TextLoader(filepath)
    docs = loader.load()
    return docs

def text_splitter(data, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(data)
    return chunks

def split_data(filepath):
    docs = load_content(filepath)
    for i, doc in enumerate(docs):
        doc.page_content = doc.page_content.strip()
        new_metadata = doc.metadata.copy()  
        new_metadata.update({
            "destination": "Văn miếu Quốc Tử Giám", "province": "Hà Nội", "type": "di tích lịch sử"
        })
        docs[i] = Document(page_content=doc.page_content, metadata=new_metadata)
    chunks = text_splitter(docs, 512, 20)
    return chunks