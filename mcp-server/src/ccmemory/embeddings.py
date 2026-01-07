"""Embedding generation for semantic search via Ollama."""

import logging
import os
import time

import httpx

logger = logging.getLogger("ccmemory.embed")

EMBEDDING_MODEL = os.getenv("CCMEMORY_OLLAMA_MODEL", "all-minilm")
EMBEDDING_DIMS = 384
OLLAMA_URL = os.getenv("CCMEMORY_OLLAMA_URL", "http://localhost:11434")

_embedding_cache = {}


def getEmbedding(text: str) -> list:
    """Generate embedding for text using Ollama."""
    if not text:
        logger.debug("Empty text, returning zero vector")
        return [0.0] * EMBEDDING_DIMS

    cache_key = hash(text)
    if cache_key in _embedding_cache:
        logger.debug(f"Cache hit for {len(text)} char text")
        return _embedding_cache[cache_key]

    logger.debug(f"getEmbedding({len(text)} chars)")
    start = time.time()
    logger.debug(f"Ollama POST /api/embeddings (model={EMBEDDING_MODEL})")

    response = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=30.0,
    )
    response.raise_for_status()
    embedding = response.json()["embedding"]

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
