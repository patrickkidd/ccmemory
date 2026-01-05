"""Embedding generation for semantic search via Ollama."""

import os

import httpx

EMBEDDING_MODEL = os.getenv("CCMEMORY_OLLAMA_MODEL", "all-minilm")
EMBEDDING_DIMS = 384
OLLAMA_URL = os.getenv("CCMEMORY_OLLAMA_URL", "http://localhost:11434")

_embedding_cache = {}


def getEmbedding(text: str) -> list:
    """Generate embedding for text using Ollama."""
    if not text:
        return [0.0] * EMBEDDING_DIMS

    cache_key = hash(text)
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    response = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=30.0,
    )
    response.raise_for_status()
    embedding = response.json()["embedding"]

    _embedding_cache[cache_key] = embedding
    return embedding


def getEmbeddings(texts: list[str]) -> list[list]:
    """Generate embeddings for multiple texts."""
    if not texts:
        return []

    results = []
    for text in texts:
        results.append(getEmbedding(text))

    return results


def clearCache():
    """Clear the embedding cache."""
    global _embedding_cache
    _embedding_cache = {}
