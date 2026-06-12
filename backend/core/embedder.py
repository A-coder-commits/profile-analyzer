"""
Text embedding using FastEmbed.

Provides text chunking (with overlap) and embedding generation
via the BAAI/bge-small-en-v1.5 model. Lightweight replacement
for sentence-transformers — same interface, ~10x smaller download.
All downstream modules call embed_texts() to get vector representations.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from fastembed import TextEmbedding

from core.config import EMBED_MODEL_NAME

logger = logging.getLogger(__name__)

# ── Model Loading ────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _get_model() -> TextEmbedding:
    """
    Lazily load and cache the FastEmbed model.

    The model is downloaded on first call and kept in memory
    for all subsequent embedding requests.
    """
    logger.info("Loading FastEmbed model: %s", EMBED_MODEL_NAME)
    return TextEmbedding(model_name=EMBED_MODEL_NAME)


# ── Chunking ─────────────────────────────────────────────────────────────────


def chunk_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks based on word count.

    Uses a simple word-based tokenization (split on whitespace) to
    approximate token counts. Each chunk contains `chunk_size` words
    with `overlap` words shared between consecutive chunks.

    Args:
        text: The full text to split.
        chunk_size: Maximum number of words per chunk.
        overlap: Number of overlapping words between chunks.

    Returns:
        A list of text chunk strings. Returns an empty list if
        the input text is empty or whitespace-only.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Advance by (chunk_size - overlap) so the next chunk
        # shares `overlap` words with the current one
        start += chunk_size - overlap

    return chunks


# ── Embedding ────────────────────────────────────────────────────────────────


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embedding vectors for a list of text strings.

    FastEmbed returns a generator — we convert it to a list of
    float lists for compatibility with ChromaDB.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).
        Dimensionality is 384 for BAAI/bge-small-en-v1.5.

    Raises:
        ValueError: If texts is empty.
    """
    if not texts:
        raise ValueError("Cannot embed an empty list of texts.")

    model = _get_model()
    embeddings = list(model.embed(texts))
    return [emb.tolist() for emb in embeddings]


def chunk_and_embed(text: str) -> tuple[list[str], list[list[float]]]:
    """
    Convenience function: chunk a text document and embed all chunks.

    Args:
        text: The full document text.

    Returns:
        A tuple of (chunks, embeddings) where chunks[i] corresponds
        to embeddings[i].
    """
    chunks = chunk_text(text)
    if not chunks:
        return [], []
    embeddings = embed_texts(chunks)
    return chunks, embeddings