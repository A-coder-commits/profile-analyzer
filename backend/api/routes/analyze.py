"""
Profile analysis endpoint.

Triggers the full RAG-powered analysis of the developer's profile
by running four structured queries against the stored resume and
GitHub data, returning strengths, weaknesses, top projects, and
a personalized learning roadmap.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from core.rag_pipeline import run_full_analysis
from core.vector_store import RESUME_COLLECTION, GITHUB_COLLECTION, get_or_create_collection
from models.schemas import (
    AnalysisResponse,
    StrengthItem,
    WeaknessItem,
    TopProject,
    RoadmapStep,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Run full profile analysis",
    responses={
        400: {"description": "No profile data loaded yet"},
        500: {"description": "Analysis pipeline failure"},
    },
)
async def analyze_profile() -> AnalysisResponse:
    """
    Run a comprehensive analysis of the developer's profile.

    Requires that resume and/or GitHub data have already been
    uploaded and stored in ChromaDB. Executes four RAG queries:
    1. Technical strengths identification
    2. Skill gaps and weaknesses
    3. Top projects by technical depth
    4. Personalized 3-month learning roadmap

    Returns structured JSON with all insights.
    """
    # ── Check that we have data to analyze ───────────────────────────────
    resume_col = get_or_create_collection(RESUME_COLLECTION)
    github_col = get_or_create_collection(GITHUB_COLLECTION)

    total_docs = resume_col.count() + github_col.count()
    if total_docs == 0:
        raise HTTPException(
            status_code=400,
            detail="No profile data found. Please upload a resume and/or GitHub profile first.",
        )

    # ── Run full analysis ────────────────────────────────────────────────
    try:
        raw_results = run_full_analysis()
    except RuntimeError as e:
        # Typically missing API key
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Analysis pipeline failed")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}. Please try again.",
        )

    # ── Parse into typed models ──────────────────────────────────────────
    try:
        strengths = [
            StrengthItem(
                title=item.get("title", "Untitled"),
                description=item.get("description", ""),
            )
            for item in raw_results.get("strengths", [])
        ]

        weaknesses = [
            WeaknessItem(
                title=item.get("title", "Untitled"),
                description=item.get("description", ""),
            )
            for item in raw_results.get("weaknesses", [])
        ]

        top_projects = [
            TopProject(
                name=item.get("name", "Unknown"),
                reason=item.get("reason", ""),
            )
            for item in raw_results.get("top_projects", [])
        ]

        roadmap = [
            RoadmapStep(
                week=item.get("week", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                resources=item.get("resources", []),
            )
            for item in raw_results.get("roadmap", [])
        ]
    except Exception as e:
        logger.exception("Failed to parse analysis results into typed models")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse analysis results: {e}",
        )

    return AnalysisResponse(
        strengths=strengths,
        weaknesses=weaknesses,
        top_projects=top_projects,
        roadmap=roadmap,
    )
