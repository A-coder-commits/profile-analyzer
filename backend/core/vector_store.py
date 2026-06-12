"""
ChromaDB vector store management.

Provides persistent storage and semantic retrieval of embedded
text chunks. Maintains two collections — one for resume data and
one for GitHub data — and exposes functions to add, query, and
reset documents.
"""

from __future__ import annotations

import logging
import uuid

import chromadb
from chromadb.config import Settings

from core.config import CHROMA_PERSIST_DIR
from core.embedder import embed_texts

logger = logging.getLogger(__name__)

# ── Collection Names ─────────────────────────────────────────────────────────

RESUME_COLLECTION = "resume_chunks"
GITHUB_COLLECTION = "github_chunks"

# ── Client Singleton ─────────────────────────────────────────────────────────

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    """
    Get or create the ChromaDB persistent client singleton.

    The client persists data to the directory specified by
    CHROMA_PERSIST_DIR in the configuration.
    """
    global _client
    if _client is None:
        logger.info("Initializing ChromaDB client at: %s", CHROMA_PERSIST_DIR)
        _client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_or_create_collection(name: str) -> chromadb.Collection:
    """
    Get an existing collection or create a new one.

    Args:
        name: The collection name (use RESUME_COLLECTION or GITHUB_COLLECTION).

    Returns:
        A ChromaDB Collection object.
    """
    client = _get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(
    collection_name: str,
    texts: list[str],
    metadatas: list[dict] | None = None,
    embeddings: list[list[float]] | None = None,
) -> int:
    """
    Add text documents to a ChromaDB collection.

    If embeddings are not provided, they are generated automatically
    using the embedder module. Each document gets a unique UUID.

    Args:
        collection_name: Target collection name.
        texts: List of text chunks to store.
        metadatas: Optional list of metadata dicts (one per text).
        embeddings: Optional pre-computed embeddings.

    Returns:
        The number of documents added.

    Raises:
        ValueError: If texts is empty.
    """
    if not texts:
        raise ValueError("Cannot add an empty list of documents.")

    collection = get_or_create_collection(collection_name)

    # Generate embeddings if not provided
    if embeddings is None:
        embeddings = embed_texts(texts)

    # Generate unique IDs
    ids = [str(uuid.uuid4()) for _ in texts]

    # Default metadata if not provided
    if metadatas is None:
        metadatas = [{"source": collection_name} for _ in texts]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info("Added %d documents to collection '%s'", len(texts), collection_name)
    return len(texts)


def query(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
) -> list[dict]:
    """
    Perform a semantic search against a ChromaDB collection.

    Embeds the query text and retrieves the most similar documents.

    Args:
        collection_name: The collection to search.
        query_text: The natural-language query string.
        n_results: Number of top results to return.

    Returns:
        A list of dicts, each with keys:
        - "text": the document content
        - "metadata": associated metadata
        - "distance": cosine distance score
    """
    collection = get_or_create_collection(collection_name)

    # Check if collection has documents
    if collection.count() == 0:
        logger.warning("Collection '%s' is empty, returning no results.", collection_name)
        return []

    query_embedding = embed_texts([query_text])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
    )

    # Flatten results into a clean list
    output: list[dict] = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            output.append(
                {
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                }
            )

    return output


def reset_collection(collection_name: str) -> None:
    """
    Delete and recreate a collection, removing all stored documents.

    Useful before a fresh analysis to avoid mixing old and new data.

    Args:
        collection_name: The collection to reset.
    """
    client = _get_client()
    try:
        client.delete_collection(collection_name)
        logger.info("Deleted collection '%s'", collection_name)
    except ValueError:
        logger.info("Collection '%s' does not exist, nothing to delete.", collection_name)

    # Recreate empty collection
    get_or_create_collection(collection_name)
    logger.info("Recreated empty collection '%s'", collection_name)


def reset_all() -> None:
    """Reset both resume and GitHub collections."""
    reset_collection(RESUME_COLLECTION)
    reset_collection(GITHUB_COLLECTION)
