"""
GitHub profile upload endpoint.

Accepts a GitHub URL or username, scrapes the profile using
the GitHub REST API, chunks and embeds the data, and stores
it in ChromaDB for downstream RAG queries.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException

from core.github_scraper import scrape_github_profile, format_github_data_for_embedding
from core.embedder import chunk_text, embed_texts
from core.vector_store import GITHUB_COLLECTION, add_documents, reset_collection
from models.schemas import GitHubUploadRequest, GitHubUploadResponse, RepoSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/github",
    response_model=GitHubUploadResponse,
    summary="Scrape and process a GitHub profile",
    responses={
        400: {"description": "Invalid GitHub URL or username"},
        403: {"description": "GitHub API rate limit exceeded"},
        404: {"description": "GitHub user not found"},
        500: {"description": "Scraping or embedding failure"},
    },
)
async def upload_github(body: GitHubUploadRequest) -> GitHubUploadResponse:
    """
    Scrape a GitHub profile and store the data for analysis.

    The endpoint performs the following steps:
    1. Extracts the username from the provided URL or string.
    2. Fetches all public repos, language stats, and top READMEs via GitHub API.
    3. Formats the data into text documents for embedding.
    4. Chunks and embeds all documents.
    5. Stores everything in the ChromaDB 'github_chunks' collection.
    6. Returns a summary of the scraped profile.
    """
    # ── Scrape GitHub profile ────────────────────────────────────────────
    try:
        profile_data = await scrape_github_profile(body.github_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user not found. Please check the URL or username.",
            )
        if e.response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="GitHub API rate limit exceeded. Please set a GITHUB_TOKEN in .env or try again later.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"GitHub API error ({e.response.status_code}): {e.response.text[:200]}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to GitHub API: {str(e)}",
        )

    # ── Format for embedding ─────────────────────────────────────────────
    documents = format_github_data_for_embedding(profile_data)

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="No data could be extracted from this GitHub profile.",
        )

    # ── Chunk and embed ──────────────────────────────────────────────────
    try:
        # Chunk each document individually, then flatten
        all_chunks: list[str] = []
        all_metadatas: list[dict] = []
        for doc in documents:
            doc_chunks = chunk_text(doc)
            all_chunks.extend(doc_chunks)
            all_metadatas.extend(
                [{"source": "github", "chunk_index": i} for i in range(len(doc_chunks))]
            )

        if not all_chunks:
            raise HTTPException(status_code=400, detail="GitHub data produced no usable content.")

        embeddings = embed_texts(all_chunks)

        # Reset old GitHub data and store fresh
        reset_collection(GITHUB_COLLECTION)
        chunks_stored = add_documents(
            GITHUB_COLLECTION,
            texts=all_chunks,
            metadatas=all_metadatas,
            embeddings=embeddings,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Embedding/storage failed for GitHub data")
        raise HTTPException(status_code=500, detail=f"Failed to process GitHub data: {e}")

    # ── Build response ───────────────────────────────────────────────────
    repos = [
        RepoSummary(
            name=r["name"],
            description=r.get("description"),
            language=r.get("language"),
            stars=r.get("stars", 0),
            forks=r.get("forks", 0),
            last_updated=r.get("last_updated"),
        )
        for r in profile_data.get("repos", [])[:20]  # Cap at 20 for response size
    ]

    return GitHubUploadResponse(
        success=True,
        username=profile_data["username"],
        total_repos=profile_data["total_repos"],
        top_languages=profile_data.get("top_languages", {}),
        repos=repos,
        chunks_stored=chunks_stored,
    )
