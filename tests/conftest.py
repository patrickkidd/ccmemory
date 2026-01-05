"""Pytest configuration and fixtures for ccmemory tests."""

import os
import sys
import pytest

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("CCMEMORY_NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("CCMEMORY_NEO4J_PASSWORD", "ccmemory")
    monkeypatch.setenv("CCMEMORY_USER_ID", "test@example.com")


@pytest.fixture
def sample_decision():
    """Sample decision data."""
    return {
        "description": "Use PostgreSQL for the main database",
        "rationale": "Better support for complex queries and JSONB",
        "options_considered": "PostgreSQL, MySQL, SQLite",
        "revisit_trigger": "If we need horizontal scaling beyond single node",
    }


@pytest.fixture
def sample_correction():
    """Sample correction data."""
    return {
        "wrong_belief": "The API returns data in XML format",
        "right_belief": "The API returns data in JSON format",
        "severity": "significant",
    }


@pytest.fixture
def sample_insight():
    """Sample insight data."""
    return {
        "category": "realization",
        "summary": "Most auth issues stem from token refresh timing",
        "implications": "Need to implement proactive token refresh before expiry",
    }


@pytest.fixture
def sample_failed_approach():
    """Sample failed approach data."""
    return {
        "approach": "Using exponential backoff for retry logic",
        "outcome": "Caused cascading failures under load",
        "lesson": "Use circuit breaker pattern instead for external services",
    }
