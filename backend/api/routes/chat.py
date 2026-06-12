"""
Follow-up chat endpoint with streaming support.

Allows the user to ask follow-up questions about their profile
using the RAG pipeline. Supports Server-Sent Events (SSE) for
real-time token streaming.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from core.rag_pipeline import rag_stream
from core.vector_store import RESUME_COLLECTION, GITHUB_COLLECTION, get_or_create_collection
from models.schemas import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    summary="Chat about your profile (streaming SSE)",
    responses={
        400: {"description": "No profile data loaded or empty message"},
        500: {"description": "Chat pipeline failure"},
    },
)
async def chat(body: ChatRequest) -> StreamingResponse:
    """
    Send a follow-up question about the developer's profile.

    Uses the RAG pipeline to retrieve relevant context from the
    stored resume and GitHub data, then streams Claude's response
    via Server-Sent Events (SSE).

    The response is an SSE stream where each event contains a
    JSON payload with a "token" field. The stream ends with a
    [DONE] event.

    Frontend should consume this with EventSource or fetch + ReadableStream.
    """
    # ── Validate data exists ─────────────────────────────────────────────
    resume_col = get_or_create_collection(RESUME_COLLECTION)
    github_col = get_or_create_collection(GITHUB_COLLECTION)

    total_docs = resume_col.count() + github_col.count()
    if total_docs == 0:
        raise HTTPException(
            status_code=400,
            detail="No profile data found. Please upload a resume and/or GitHub profile first.",
        )

    # ── Build history for multi-turn ─────────────────────────────────────
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in body.history
    ]

    # ── Stream response via SSE ──────────────────────────────────────────
    async def event_generator():
        """Generate SSE events from the RAG stream."""
        try:
            async for token in rag_stream(body.message, history=history):
                data = json.dumps({"token": token})
                yield f"data: {data}\n\n"

            # Signal end of stream
            yield "data: [DONE]\n\n"

        except RuntimeError as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("Chat streaming failed")
            error_data = json.dumps({"error": f"Chat failed: {str(e)}"})
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
