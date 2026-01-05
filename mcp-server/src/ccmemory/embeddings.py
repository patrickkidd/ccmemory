"""Embedding generation for semantic search via Voyage AI."""

import os

EMBEDDING_MODEL = "voyage-3"
EMBEDDING_DIMS = 1024

_voyage_client = None
_embedding_cache = {}
_voyageai = None


def _getVoyageClient():
    global _voyage_client, _voyageai
    if _voyage_client is None:
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError("VOYAGE_API_KEY environment variable not set")
        if _voyageai is None:
            import voyageai
            _voyageai = voyageai
        _voyage_client = _voyageai.Client(api_key=api_key)
    return _voyage_client


def getEmbedding(text: str) -> list:
    """Generate embedding for text using Voyage AI."""
    if not text:
        return [0.0] * EMBEDDING_DIMS

    cache_key = hash(text)
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    client = _getVoyageClient()
    result = client.embed(
        texts=[text],
        model=EMBEDDING_MODEL,
        input_type="document"
    )
    embedding = result.embeddings[0]
    _embedding_cache[cache_key] = embedding
    return embedding


def getEmbeddings(texts: list[str]) -> list[list]:
    """Generate embeddings for multiple texts (batched)."""
    if not texts:
        return []

    uncached_texts = []
    uncached_indices = []
    results = [None] * len(texts)

    for i, text in enumerate(texts):
        if not text:
            results[i] = [0.0] * EMBEDDING_DIMS
            continue

        cache_key = hash(text)
        if cache_key in _embedding_cache:
            results[i] = _embedding_cache[cache_key]
        else:
            uncached_texts.append(text)
            uncached_indices.append(i)

    if uncached_texts:
        client = _getVoyageClient()
        response = client.embed(
            texts=uncached_texts,
            model=EMBEDDING_MODEL,
            input_type="document"
        )

        for j, embedding in enumerate(response.embeddings):
            idx = uncached_indices[j]
            results[idx] = embedding
            cache_key = hash(uncached_texts[j])
            _embedding_cache[cache_key] = embedding

    return results


def clearCache():
    """Clear the embedding cache."""
    global _embedding_cache
    _embedding_cache = {}
