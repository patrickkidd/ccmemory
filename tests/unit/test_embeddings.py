"""Unit tests for embeddings module."""

import sys
import pytest


pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 14),
    reason="voyageai package incompatible with Python 3.14 pydantic v1"
)


@pytest.mark.unit
def test_embedding_constants():
    """Test embedding configuration constants."""
    from ccmemory.embeddings import EMBEDDING_DIMS, EMBEDDING_MODEL
    assert EMBEDDING_DIMS == 1024
    assert EMBEDDING_MODEL == "voyage-3"


@pytest.mark.unit
def test_clear_cache():
    """Test cache clearing doesn't raise."""
    from ccmemory.embeddings import clearCache
    clearCache()
