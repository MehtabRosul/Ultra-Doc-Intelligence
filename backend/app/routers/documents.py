"""
API router for document operations: upload, ask, extract.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.schemas import (
    AskRequest,
    AskResponse,
    ExtractRequest,
    ExtractResponse,
    ShipmentData,
    SourceChunk,
    UploadResponse,
)
from app.services.document_processor import process_document, document_exists
from app.services.rag_service import ask_question, generate_suggested_questions
from app.services.extraction_service import extract_shipment_data
from app.config import ALLOWED_EXTENSIONS

import os

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a logistics document (PDF, DOCX, or TXT).
    Parses, chunks, embeds, and stores in FAISS vector index.
    File is encrypted at rest with AES-256-GCM.
    """
    # Validate file type
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        result = await process_document(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}",
        )

    # Generate suggested questions
    questions = generate_suggested_questions(result["document_id"])

    return UploadResponse(
        document_id=result["document_id"],
        filename=result["filename"],
        num_chunks=result["num_chunks"],
        message=f"Document uploaded and processed successfully. {result['num_chunks']} chunks created.",
        suggested_questions=questions,
    )


@router.post("/ask", response_model=AskResponse)
async def ask_about_document(request: AskRequest):
    """
    Ask a natural language question about an uploaded document.
    Uses RAG with guardrails and returns answer + sources + confidence.
    """
    if not document_exists(request.document_id):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found. Please upload a document first.",
        )

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = await ask_question(request.document_id, request.question)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}",
        )

    sources = [
        SourceChunk(text=s["text"], similarity_score=round(s["similarity_score"], 3))
        for s in result["sources"]
    ]

    return AskResponse(
        answer=result["answer"],
        sources=sources,
        confidence=result["confidence"],
        guardrail_status=result["guardrail_status"],
    )


@router.post("/extract", response_model=ExtractResponse)
async def extract_structured_data(request: ExtractRequest):
    """
    Extract structured shipment data from an uploaded document.
    Returns JSON with 11 fields (null if not found).
    """
    if not document_exists(request.document_id):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found. Please upload a document first.",
        )

    try:
        result = await extract_shipment_data(request.document_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting data: {str(e)}",
        )

    return ExtractResponse(
        document_id=request.document_id,
        data=ShipmentData(**result["data"]),
        confidence=result["confidence"],
    )
