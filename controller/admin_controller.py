from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Path
from typing import List, Optional
from datetime import datetime
from langchain_classic.retrievers import ParentDocumentRetriever
from RAG.core.dependencies import get_parent_document_retriever
from middleware.auth_jwt import get_current_user_payload_strict
from RAG.utils.data_service import DataService

router = APIRouter(prefix="/admin/knowledge")


def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# API Import Excel
@router.post("/import-excel")
async def import_excel(
    file: UploadFile = File(...),
    file_id: str = Form(...),
    valid_from: Optional[str] = Form(None),
    retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
    user_payload: dict = Depends(get_current_user_payload_strict),
):
    if user_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be Excel format")

    updated_at = get_current_timestamp()
    valid_from_value = valid_from if valid_from else updated_at

    try:
        await DataService.ingest_excel(
            file,
            file_id,
            retriever,
            extra_metadata={"updated_at": updated_at, "valid_from": valid_from_value},
        )
        return {"status": "success", "message": f"Successfully imported documents from Excel file."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# API Import Unstructured file (PDF, Word, Txt)
@router.post("/import-file")
async def import_file(
    file: UploadFile = File(...),
    file_id: str = Form(...),
    topic: str = Form(...),
    location: str = Form(...),
    name: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
    valid_from: Optional[str] = Form(None),
    user_payload: dict = Depends(get_current_user_payload_strict),
):
    if user_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    updated_at = get_current_timestamp()
    valid_from_value = valid_from if valid_from else updated_at
    year_str = str(datetime.now().year)

    # Gom metadata từ Form vào dict
    metadata = {
        "Topic": topic,
        "Location": location,
        "Name": name if name else file.filename,
        "Source": source if source else "Unknown",
        "updated_at": updated_at,
        "valid_from": valid_from_value,
        "year": year_str,
    }

    try:
        DataService.ingest_unstructured_file(file, file_id, metadata, retriever)
        return {"status": "success", "message": f"File '{file.filename}' imported successfully."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# API Delete
@router.delete("/{file_id}")
async def delete_knowledge(
    file_id: str = Path(...),
    retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
    user_payload: dict = Depends(get_current_user_payload_strict),
):
    if user_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    try:
        DataService.delete_document(file_id, retriever)
        return {"status": "success", "message": f"Document {file_id} has been deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# API Update
@router.put("/{file_id}")
async def update_knowledge_file(
    file_id: str = Path(...),
    file: UploadFile = File(...),
    topic: str = Form(...),
    location: str = Form(...),
    name: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    valid_from: Optional[str] = Form(None),
    retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
    user_payload: dict = Depends(get_current_user_payload_strict),
):
    if user_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    try:
        # Xóa cái cũ
        DataService.delete_document(file_id, retriever)

        updated_at = get_current_timestamp()
        valid_from_value = valid_from if valid_from else updated_at
        year_str = str(datetime.now().year)

        # Thêm cái mới
        metadata = {
            "Topic": topic,
            "Location": location,
            "Name": name if name else file.filename,
            "Source": source if source else "Unknown",
            "updated_at": updated_at,
            "valid_from": valid_from_value,
            "year": year_str,
        }
        DataService.ingest_unstructured_file(file, file_id, metadata, retriever)

        return {
            "status": "success",
            "message": "Document updated successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("", status_code=200)
async def get_all_knowledge(
    retriever: ParentDocumentRetriever = Depends(get_parent_document_retriever),
    user_payload: dict = Depends(get_current_user_payload_strict),
):
    """
    Lấy danh sách tất cả các file tài liệu đã được import vào hệ thống RAG.
    """
    if user_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    try:
        documents = DataService.get_all_files(retriever)
        return {"status": "success", "data": documents, "total": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")
