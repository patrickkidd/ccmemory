"""E2E test for ProjectFact detection and surfacing."""

import os
import uuid
import pytest
from datetime import datetime

from ccmemory.graph import GraphClient
from ccmemory.hooks import handleSessionStart, handleMessageResponse
from ccmemory.embeddings import getEmbedding


@pytest.fixture
def client():
    os.environ.setdefault("CCMEMORY_NEO4J_URI", "bolt://localhost:7687")
    os.environ.setdefault("CCMEMORY_NEO4J_PASSWORD", "ccmemory")
    os.environ.setdefault("CCMEMORY_USER_ID", "test@example.com")

    client = GraphClient()
    yield client
    client.close()


@pytest.fixture
def test_project():
    return f"e2e-project-{uuid.uuid4().hex[:8]}"


@pytest.mark.e2e
def test_project_fact_full_flow(client, test_project, tmp_path):
    session_id_1 = f"e2e-session-{uuid.uuid4().hex[:8]}"
    cwd = f"/fake/path/{test_project}"

    # Step 1: Start first session
    result1 = handleSessionStart(session_id_1, cwd)
    assert result1["project"] == test_project
    assert "No prior context" in result1["context"]

    # Step 2: Create a ProjectFact directly (simulating detection)
    fact_id = f"projectfact-{uuid.uuid4().hex[:8]}"
    embedding = getEmbedding("Uses pytest for testing")

    client.createProjectFact(
        fact_id=fact_id,
        session_id=session_id_1,
        category="tool",
        fact="Uses pytest for testing",
        embedding=embedding,
        context="testing framework",
    )

    # Step 3: Verify fact exists in graph
    facts = client.queryProjectFacts(test_project, limit=10)
    assert len(facts) >= 1
    found = any(f.get("id") == fact_id for f in facts)
    assert found

    # Step 4: Start a NEW session - fact should be surfaced
    session_id_2 = f"e2e-session-{uuid.uuid4().hex[:8]}"
    result2 = handleSessionStart(session_id_2, cwd)

    assert "## Project Conventions" in result2["context"]
    assert "Uses pytest for testing" in result2["context"]
    assert "[tool]" in result2["context"]


@pytest.mark.e2e
def test_project_fact_deduplication(client, test_project):
    session_id = f"e2e-session-{uuid.uuid4().hex[:8]}"
    cwd = f"/fake/path/{test_project}"

    handleSessionStart(session_id, cwd)

    # Create first fact
    fact1_id = f"projectfact-{uuid.uuid4().hex[:8]}"
    embedding1 = getEmbedding("Uses uv for package management")

    client.createProjectFact(
        fact_id=fact1_id,
        session_id=session_id,
        category="tool",
        fact="Uses uv for package management",
        embedding=embedding1,
    )

    # Verify fact exists
    exists = client.projectFactExists(test_project, embedding1, threshold=0.9)
    assert exists, "Original fact should exist"

    # Very similar embedding should be detected as duplicate
    embedding_similar = getEmbedding("Uses uv as package manager")
    exists_similar = client.projectFactExists(test_project, embedding_similar, threshold=0.85)
    assert exists_similar, "Semantically similar fact should be detected"

    # Different fact should not be detected
    embedding_different = getEmbedding("Uses Docker for containerization")
    exists_different = client.projectFactExists(test_project, embedding_different, threshold=0.9)
    assert not exists_different, "Different fact should not be detected as duplicate"
