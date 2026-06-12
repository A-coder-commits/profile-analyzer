"""
RAG (Retrieval-Augmented Generation) pipeline.

Orchestrates the full flow:
  1. Retrieve relevant chunks from ChromaDB (resume + GitHub)
  2. Build a context string from retrieved chunks
  3. Call Groq LLM with the context and user query
  4. Return the structured or free-form answer

Used by both the /analyze and /chat endpoints.
"""

from __future__ import annotations

import json
import logging
import re
from typing import AsyncGenerator

from groq import AsyncGroq, Groq

from core.config import GROQ_API_KEY, GROQ_MODEL
from core.vector_store import GITHUB_COLLECTION, RESUME_COLLECTION, query

logger = logging.getLogger(__name__)

# ── System Prompts ───────────────────────────────────────────────────────────

ANALYST_SYSTEM_PROMPT = """\
You are a senior career and technical mentor who specializes in analyzing \
developer profiles. You have deep expertise in software engineering, \
open-source contributions, and career development.

You are given context from a developer's resume and GitHub profile. \
Use this context to provide accurate, specific, and actionable insights. \
Be honest and constructive — highlight genuine strengths, be direct about \
gaps, and give practical advice.

Rules:
- Base your analysis ONLY on the provided context. Do not fabricate information.
- Be specific: reference actual technologies, projects, and experience from the profile.
- Be constructive: frame weaknesses as growth opportunities.
- If the context is insufficient to answer a question, say so explicitly.
"""

ANALYSIS_SYSTEM_PROMPT = """\
You are a senior career and technical mentor analyzing a developer's profile.

You will be asked structured analysis questions. For each question, respond \
with a JSON array. Each item in the array should be an object with the exact \
keys specified in the question.

Rules:
- Base analysis ONLY on the provided context from the developer's resume and GitHub.
- Be specific and reference actual technologies, projects, and experience.
- Return ONLY valid JSON — no markdown fences, no explanation text outside the JSON.
- If context is insufficient, return a shorter array rather than fabricating data.
"""

# ── Retrieval ────────────────────────────────────────────────────────────────


def retrieve(query_text: str, n_results: int = 5) -> list[dict]:
    """
    Query both resume and GitHub collections and merge results.

    Retrieves the top chunks from each collection, deduplicates,
    and returns them sorted by relevance (lowest distance first).

    Args:
        query_text: The natural-language query.
        n_results: Number of results to fetch per collection.

    Returns:
        A merged list of result dicts with 'text', 'metadata', 'distance'.
    """
    resume_results = query(RESUME_COLLECTION, query_text, n_results=n_results)
    github_results = query(GITHUB_COLLECTION, query_text, n_results=n_results)

    seen_texts: set[str] = set()
    merged: list[dict] = []
    for result in resume_results + github_results:
        text = result["text"]
        if text not in seen_texts:
            seen_texts.add(text)
            merged.append(result)

    merged.sort(key=lambda r: r.get("distance", 0.0))
    return merged


def build_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM.

    Each chunk is labeled with its source (resume or GitHub)
    and numbered for easy reference.

    Args:
        chunks: List of result dicts from retrieve().

    Returns:
        A formatted context string.
    """
    if not chunks:
        return "No relevant context found in the developer's profile."

    context_parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", "unknown")
        context_parts.append(
            f"--- Context Chunk {i} [Source: {source}] ---\n{chunk['text']}"
        )

    return "\n\n".join(context_parts)


# ── LLM Calls ────────────────────────────────────────────────────────────────


def _get_client() -> Groq:
    """
    Create a synchronous Groq client.

    Returns:
        A configured Groq client instance.

    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please add it to your .env file."
        )
    return Groq(api_key=GROQ_API_KEY)


def _get_async_client() -> AsyncGroq:
    """
    Create an asynchronous Groq client for streaming.

    Returns:
        A configured AsyncGroq client instance.

    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please add it to your .env file."
        )
    return AsyncGroq(api_key=GROQ_API_KEY)


def ask_groq(
    query_text: str,
    context: str,
    system_prompt: str = ANALYST_SYSTEM_PROMPT,
) -> str:
    """
    Call Groq with a query and retrieved context.

    Constructs a user message that includes the context and the
    specific question, then returns Groq's response.

    Args:
        query_text: The user's question or analysis prompt.
        context: The formatted context string from build_context().
        system_prompt: The system prompt defining Groq's role.

    Returns:
        Groq's text response.

    Raises:
        RuntimeError: If the API key is missing.
    """
    client = _get_client()

    user_message = (
        f"Here is the developer's profile context:\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"Question: {query_text}"
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=2048,
        temperature=0.7,
    )

    return response.choices[0].message.content


async def stream_groq(
    query_text: str,
    context: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream a response from Groq token-by-token.

    Used by the /chat endpoint for real-time streaming. Includes
    chat history for multi-turn conversations.

    Args:
        query_text: The user's latest message.
        context: The formatted context string from build_context().
        history: Optional list of previous {"role", "content"} messages.

    Yields:
        Individual text chunks as they arrive from the API.
    """
    client = _get_async_client()

    messages: list[dict] = [{"role": "system", "content": ANALYST_SYSTEM_PROMPT}]

    # Inject prior conversation history
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Append current user message with context
    user_message = (
        f"Here is the developer's profile context:\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"{query_text}"
    )
    messages.append({"role": "user", "content": user_message})

    stream = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=2048,
        temperature=0.7,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ── Full RAG Pipeline ────────────────────────────────────────────────────────


def rag_query(query_text: str, system_prompt: str = ANALYST_SYSTEM_PROMPT) -> str:
    """
    Execute the full RAG pipeline: retrieve → build context → ask Groq.

    This is the primary entry point for analysis queries.

    Args:
        query_text: The question to answer using the developer's profile.
        system_prompt: The system prompt for Groq.

    Returns:
        Groq's text response grounded in the retrieved context.
    """
    chunks = retrieve(query_text)
    context = build_context(chunks)
    return ask_groq(query_text, context, system_prompt=system_prompt)


def rag_query_json(query_text: str) -> str:
    """
    Execute RAG with the JSON-focused system prompt.

    Used for structured analysis queries where we expect
    Groq to return valid JSON.

    Args:
        query_text: The analysis question expecting a JSON response.

    Returns:
        Groq's JSON response string.
    """
    return rag_query(query_text, system_prompt=ANALYSIS_SYSTEM_PROMPT)


async def rag_stream(
    query_text: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Execute the full RAG pipeline with streaming response.

    Used by the /chat endpoint.

    Args:
        query_text: The user's question.
        history: Optional chat history.

    Yields:
        Text tokens from Groq's streaming response.
    """
    chunks = retrieve(query_text)
    context = build_context(chunks)
    async for token in stream_groq(query_text, context, history=history):
        yield token


# ── Analysis Queries ─────────────────────────────────────────────────────────

STRENGTHS_QUERY = """\
What are this developer's strongest technical skills based on their resume and \
GitHub profile? Consider: languages they use most, complexity of projects, \
depth of experience, and any standout achievements.

Respond with a JSON array of objects. Each object must have:
- "title": a short label (2-5 words)
- "description": a detailed explanation (2-3 sentences)

Return 4-6 items. Example format:
[{"title": "...", "description": "..."}]
"""

WEAKNESSES_QUERY = """\
What technologies, concepts, or skills does this developer lack experience in \
or show gaps? Consider: missing modern practices, limited tech breadth, \
areas where their projects could be stronger, and industry-standard skills \
not evident in their profile.

Respond with a JSON array of objects. Each object must have:
- "title": a short label (2-5 words)
- "description": a detailed explanation of the gap and why it matters (2-3 sentences)

Return 4-6 items. Example format:
[{"title": "...", "description": "..."}]
"""

TOP_PROJECTS_QUERY = """\
Which projects from this developer's GitHub profile show the most technical \
depth and sophistication? Consider: architecture, problem complexity, \
documentation quality, stars/engagement, and technology choices.

Respond with a JSON array of objects. Each object must have:
- "name": the repository or project name
- "reason": why this project stands out technically (2-3 sentences)

Return 3-5 items. Example format:
[{"name": "...", "reason": "..."}]
"""

ROADMAP_QUERY = """\
Based on this developer's current skills and gaps, create a personalized \
3-month learning roadmap. The roadmap should address their weaknesses, \
build on their strengths, and include practical projects.

Respond with a JSON array of objects. Each object must have:
- "week": a time range (e.g., "Week 1-2")
- "title": what to learn or build (short label)
- "description": detailed action items (2-3 sentences)
- "resources": array of 2-3 suggested resources (course names, documentation links, or book titles)

Return 5-7 items covering the full 3 months. Example format:
[{"week": "Week 1-2", "title": "...", "description": "...", "resources": ["...", "..."]}]
"""


def run_full_analysis() -> dict:
    """
    Run all four analysis queries and parse the results.

    Executes the RAG pipeline for strengths, weaknesses, top projects,
    and roadmap. Parses JSON responses and returns a structured dict.

    Returns:
        A dict with keys: strengths, weaknesses, top_projects, roadmap.
        Each value is a list of dicts matching the AnalysisResponse schema.
    """
    results: dict = {
        "strengths": [],
        "weaknesses": [],
        "top_projects": [],
        "roadmap": [],
    }

    queries = {
        "strengths": STRENGTHS_QUERY,
        "weaknesses": WEAKNESSES_QUERY,
        "top_projects": TOP_PROJECTS_QUERY,
        "roadmap": ROADMAP_QUERY,
    }

    for key, query_text in queries.items():
        try:
            raw_response = rag_query_json(query_text)
            parsed = _parse_json_response(raw_response)
            if isinstance(parsed, list):
                results[key] = parsed
            else:
                logger.warning("Expected list for %s, got %s", key, type(parsed))
                results[key] = [parsed] if parsed else []
        except Exception as e:
            logger.error("Failed to get %s analysis: %s", key, str(e))
            results[key] = []

    return results


def _parse_json_response(text: str) -> list | dict:
    """
    Parse a JSON response from Groq, handling common formatting issues.

    Groq sometimes wraps JSON in markdown fences or adds explanation
    text. This function extracts and parses the JSON portion.

    Args:
        text: Raw response text from Groq.

    Returns:
        Parsed JSON as a Python list or dict.

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code fences
    json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find array or object boundaries
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(text[start_idx : end_idx + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not parse JSON from response: {text[:200]}...")