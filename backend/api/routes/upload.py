"""
Resume upload endpoint.

Accepts a multipart PDF file, extracts text via PyMuPDF,
chunks and embeds the content, and stores it in ChromaDB
for downstream RAG queries.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File

from core.config import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB, TEMP_DIR
from core.pdf_extractor import extract_text_from_pdf
from core.embedder import chunk_text, embed_texts
from core.vector_store import RESUME_COLLECTION, add_documents, reset_collection
from models.schemas import ResumeUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/resume",
    response_model=ResumeUploadResponse,
    summary="Upload and process a PDF resume",
    responses={
        400: {"description": "Invalid file type or file too large"},
        500: {"description": "PDF extraction or embedding failure"},
    },
)
async def upload_resume(file: UploadFile = File(..., description="PDF resume file")) -> ResumeUploadResponse:
    """
    Upload a PDF resume for analysis.

    The endpoint performs the following steps:
    1. Validates the file type (must be PDF) and size (max 10MB).
    2. Saves the file temporarily to disk.
    3. Extracts text using PyMuPDF.
    4. Chunks the text into overlapping segments.
    5. Embeds all chunks using sentence-transformers.
    6. Stores chunks + embeddings in the ChromaDB 'resume_chunks' collection.
    7. Returns a success response with extraction stats and a text preview.
    """
    # ── Validate file type ───────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a .pdf file.",
        )

    # ── Validate file size ───────────────────────────────────────────────
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB.",
        )

    # ── Save temporarily ─────────────────────────────────────────────────
    temp_path = TEMP_DIR / "resume.pdf"
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # ── Extract text ─────────────────────────────────────────────────────
    try:
        text, page_count = extract_text_from_pdf(temp_path)
    except (FileNotFoundError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {e}")

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the PDF. The file may be image-based or corrupted.",
        )

    # ── Chunk and embed ──────────────────────────────────────────────────
    try:
        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Text extraction produced no usable content.")

        embeddings = embed_texts(chunks)

        # Reset old resume data and store fresh
        reset_collection(RESUME_COLLECTION)
        metadatas = [{"source": "resume", "chunk_index": i} for i in range(len(chunks))]
        chunks_stored = add_documents(
            RESUME_COLLECTION,
            texts=chunks,
            metadatas=metadatas,
            embeddings=embeddings,
        )
    except Exception as e:
        logger.exception("Embedding/storage failed")
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {e}")

    # ── Build response ───────────────────────────────────────────────────
    text_preview = text[:500] + ("..." if len(text) > 500 else "")

    return ResumeUploadResponse(
        success=True,
        filename=file.filename,
        pages_extracted=page_count,
        chunks_stored=chunks_stored,
        text_preview=text_preview,
    )
