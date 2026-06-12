"""
Pydantic request/response models for the Developer Profile Analyzer API.

Defines typed schemas for every endpoint's input and output,
ensuring strict validation and auto-generated OpenAPI docs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


# ── Request Models ───────────────────────────────────────────────────────────


class GitHubUploadRequest(BaseModel):
    """Request body for the GitHub profile upload endpoint."""

    github_url: str = Field(
        ...,
        description="GitHub profile URL or username (e.g. 'https://github.com/torvalds' or 'torvalds')",
        examples=["https://github.com/torvalds", "torvalds"],
    )


class ChatRequest(BaseModel):
    """Request body for the follow-up chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's follow-up question about their profile",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation turns for context",
    )


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


# Fix forward reference — ChatRequest references ChatMessage
ChatRequest.model_rebuild()


# ── Response Models ──────────────────────────────────────────────────────────


class ResumeUploadResponse(BaseModel):
    """Response from the resume upload endpoint."""

    success: bool = True
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    pages_extracted: int = Field(..., description="Number of pages processed")
    chunks_stored: int = Field(..., description="Number of text chunks embedded and stored")
    text_preview: str = Field(
        ...,
        description="First 500 characters of extracted text as a preview",
    )


class RepoSummary(BaseModel):
    """Summary of a single GitHub repository."""

    name: str
    description: str | None = None
    language: str | None = None
    stars: int = 0
    forks: int = 0
    last_updated: str | None = None


class GitHubUploadResponse(BaseModel):
    """Response from the GitHub profile upload endpoint."""

    success: bool = True
    username: str
    total_repos: int
    top_languages: dict[str, int] = Field(
        default_factory=dict,
        description="Language → repo count mapping, sorted by frequency",
    )
    repos: list[RepoSummary] = Field(
        default_factory=list,
        description="List of repository summaries",
    )
    chunks_stored: int = Field(..., description="Number of text chunks embedded and stored")


class StrengthItem(BaseModel):
    """A single strength identified in the developer's profile."""

    title: str = Field(..., description="Short label for the strength")
    description: str = Field(..., description="Detailed explanation")


class WeaknessItem(BaseModel):
    """A single gap/weakness identified in the developer's profile."""

    title: str = Field(..., description="Short label for the gap")
    description: str = Field(..., description="Detailed explanation and why it matters")


class TopProject(BaseModel):
    """A project showing notable technical depth."""

    name: str = Field(..., description="Repository or project name")
    reason: str = Field(..., description="Why this project stands out technically")


class RoadmapStep(BaseModel):
    """A single step in the personalized learning roadmap."""

    week: str = Field(..., description="Time range, e.g. 'Week 1-2'")
    title: str = Field(..., description="What to learn or build")
    description: str = Field(..., description="Detailed action items")
    resources: list[str] = Field(
        default_factory=list,
        description="Suggested learning resources (links, courses, docs)",
    )


class AnalysisResponse(BaseModel):
    """Full profile analysis response containing all insights."""

    strengths: list[StrengthItem] = Field(default_factory=list)
    weaknesses: list[WeaknessItem] = Field(default_factory=list)
    top_projects: list[TopProject] = Field(default_factory=list)
    roadmap: list[RoadmapStep] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from the chat endpoint (non-streaming fallback)."""

    reply: str = Field(..., description="Assistant's response text")


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str = Field(..., description="Human-readable error message")
