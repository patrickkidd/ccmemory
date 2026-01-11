"""Embedding generation for semantic search via Ollama."""

import logging
import os
import time

import httpx

logger = logging.getLogger("ccmemory.embed")

EMBEDDING_MODEL = os.getenv("CCMEMORY_OLLAMA_MODEL", "nomic-embed-text")
EMBEDDING_DIMS = 768
OLLAMA_URL = os.getenv("CCMEMORY_OLLAMA_URL", "http://localhost:11434")
MAX_TEXT_LENGTH = 8000  # Truncate long texts to avoid model limits

_embedding_cache = {}


def getEmbedding(text: str) -> list:
    """Generate embedding for text using Ollama."""
    if not text:
        raise ValueError("Cannot generate embedding for empty text")

    # Truncate long texts
    if len(text) > MAX_TEXT_LENGTH:
        logger.debug(f"Truncating text from {len(text)} to {MAX_TEXT_LENGTH} chars")
        text = text[:MAX_TEXT_LENGTH]

    cache_key = hash(text)
    if cache_key in _embedding_cache:
        logger.debug(f"Cache hit for {len(text)} char text")
        return _embedding_cache[cache_key]

    logger.debug(f"getEmbedding({len(text)} chars)")
    start = time.time()
    logger.debug(f"Ollama POST /api/embeddings (model={EMBEDDING_MODEL})")

    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30.0,
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Ollama embedding failed: {e.response.status_code}") from e

    duration = int((time.time() - start) * 1000)
    logger.debug(f"Embedding: {len(embedding)} dims, {duration}ms")

    _embedding_cache[cache_key] = embedding
    return embedding


def getEmbeddings(texts: list[str]) -> list[list]:
    """Generate embeddings for multiple texts."""
    if not texts:
        return []

    logger.debug(f"getEmbeddings({len(texts)} texts)")
    results = []
    for text in texts:
        results.append(getEmbedding(text))

    return results


def clearCache():
    """Clear the embedding cache."""
    global _embedding_cache
    logger.debug(f"Clearing cache ({len(_embedding_cache)} entries)")
    _embedding_cache = {}
