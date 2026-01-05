"""Unit tests for embeddings module."""

import pytest


@pytest.mark.unit
def test_embedding_constants():
    """Test embedding configuration constants."""
    from ccmemory.embeddings import EMBEDDING_DIMS, EMBEDDING_MODEL
    assert EMBEDDING_DIMS == 384
    assert EMBEDDING_MODEL == "all-minilm"


@pytest.mark.unit
def test_clear_cache():
    """Test cache clearing doesn't raise."""
    from ccmemory.embeddings import clearCache
    clearCache()
