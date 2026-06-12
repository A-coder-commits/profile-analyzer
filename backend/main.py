"""
Developer Profile Analyzer — FastAPI Application Entry Point.

Mounts all API routers, configures CORS for the Next.js frontend,
and provides the Uvicorn entry point.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import upload, github, analyze, chat

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Developer Profile Analyzer",
    description=(
        "Upload your resume and GitHub profile to receive AI-powered insights: "
        "strengths, weaknesses, skill gaps, and a personalized learning roadmap."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "https://profile-analyzer-pi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(upload.router)
app.include_router(github.router)
app.include_router(analyze.router)
app.include_router(chat.router)


# ── Health Check ─────────────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "Developer Profile Analyzer"}


# ── Uvicorn Entry Point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
