"""Integration tests for Neo4j graph client."""

import os
import uuid
import pytest

from ccmemory.graph import GraphClient


@pytest.fixture
def client():
    """Create a graph client for testing."""
    os.environ.setdefault("CCMEMORY_NEO4J_URI", "bolt://localhost:7687")
    os.environ.setdefault("CCMEMORY_NEO4J_PASSWORD", "ccmemory")
    os.environ.setdefault("CCMEMORY_USER_ID", "test@example.com")

    client = GraphClient()
    yield client
    client.close()


@pytest.fixture
def test_project():
    """Generate a unique test project name."""
    return f"test-project-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_session_id():
    """Generate a unique test session ID."""
    return f"test-session-{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
def test_create_session(client, test_project, test_session_id):
    """Test creating a session."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    with client.driver.session() as session:
        result = session.run(
            "MATCH (s:Session {id: $id}) RETURN s",
            id=test_session_id
        )
        record = result.single()
        assert record is not None
        assert record["s"]["project"] == test_project


@pytest.mark.integration
def test_create_decision(client, test_project, test_session_id):
    """Test creating a decision linked to a session."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    decision_id = f"decision-{uuid.uuid4().hex[:8]}"
    embedding = [0.0] * 1024

    client.createDecision(
        decision_id=decision_id,
        session_id=test_session_id,
        description="Test decision",
        embedding=embedding,
        rationale="Testing"
    )

    with client.driver.session() as session:
        result = session.run(
            "MATCH (s:Session)-[:DECIDED]->(d:Decision {id: $id}) RETURN d, s",
            id=decision_id
        )
        record = result.single()
        assert record is not None
        assert record["d"]["description"] == "Test decision"
        assert record["d"]["status"] == "developmental"


@pytest.mark.integration
def test_create_correction(client, test_project, test_session_id):
    """Test creating a correction linked to a session."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    correction_id = f"correction-{uuid.uuid4().hex[:8]}"
    embedding = [0.0] * 1024

    client.createCorrection(
        correction_id=correction_id,
        session_id=test_session_id,
        wrong_belief="Wrong thing",
        right_belief="Right thing",
        embedding=embedding,
        severity="significant"
    )

    with client.driver.session() as session:
        result = session.run(
            "MATCH (s:Session)-[:CORRECTED]->(c:Correction {id: $id}) RETURN c",
            id=correction_id
        )
        record = result.single()
        assert record is not None
        assert record["c"]["wrong_belief"] == "Wrong thing"
        assert record["c"]["right_belief"] == "Right thing"


@pytest.mark.integration
def test_query_recent(client, test_project, test_session_id):
    """Test querying recent context."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    decision_id = f"decision-{uuid.uuid4().hex[:8]}"
    embedding = [0.0] * 1024

    client.createDecision(
        decision_id=decision_id,
        session_id=test_session_id,
        description="Query test decision",
        embedding=embedding
    )

    results = client.queryRecent(test_project, limit=10)
    assert len(results) > 0

    found = False
    for r in results:
        if r.get("n", {}).get("id") == decision_id:
            found = True
            break
    assert found


@pytest.mark.integration
def test_get_all_metrics(client, test_project, test_session_id):
    """Test getting all metrics."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    metrics = client.getAllMetrics(test_project)

    assert "cognitive_coefficient" in metrics
    assert "total_decisions" in metrics
    assert "total_corrections" in metrics
    assert "total_sessions" in metrics
    assert metrics["cognitive_coefficient"] >= 1.0


@pytest.mark.integration
def test_record_telemetry(client, test_project):
    """Test recording telemetry events."""
    client.recordTelemetry(
        event_type="test_event",
        project=test_project,
        data={"count": 5, "types": ["a", "b"]}
    )

    with client.driver.session() as session:
        result = session.run(
            "MATCH (t:TelemetryEvent {project: $project, event_type: 'test_event'}) RETURN t",
            project=test_project
        )
        record = result.single()
        assert record is not None
        assert record["t"]["count"] == 5


@pytest.mark.integration
def test_create_project_fact(client, test_project, test_session_id):
    """Test creating a project fact linked to a session."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    fact_id = f"projectfact-{uuid.uuid4().hex[:8]}"
    embedding = [0.1] * 384

    client.createProjectFact(
        fact_id=fact_id,
        session_id=test_session_id,
        category="tool",
        fact="Uses pytest for testing",
        embedding=embedding,
        context="testing framework"
    )

    with client.driver.session() as session:
        result = session.run(
            "MATCH (s:Session)-[:STATED]->(pf:ProjectFact {id: $id}) RETURN pf",
            id=fact_id
        )
        record = result.single()
        assert record is not None
        assert record["pf"]["fact"] == "Uses pytest for testing"
        assert record["pf"]["category"] == "tool"


@pytest.mark.integration
def test_query_project_facts(client, test_project, test_session_id):
    """Test querying project facts."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    fact_id = f"projectfact-{uuid.uuid4().hex[:8]}"
    embedding = [0.1] * 384

    client.createProjectFact(
        fact_id=fact_id,
        session_id=test_session_id,
        category="convention",
        fact="Uses camelCase for functions",
        embedding=embedding
    )

    results = client.queryProjectFacts(test_project, limit=10)
    assert len(results) > 0

    found = False
    for r in results:
        if r.get("id") == fact_id:
            found = True
            assert r.get("fact") == "Uses camelCase for functions"
            break
    assert found


@pytest.mark.integration
def test_project_fact_exists(client, test_project, test_session_id):
    """Test semantic deduplication of project facts."""
    from datetime import datetime
    import random

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    fact_id = f"projectfact-{uuid.uuid4().hex[:8]}"
    random.seed(42)
    embedding = [random.uniform(-1, 1) for _ in range(384)]

    client.createProjectFact(
        fact_id=fact_id,
        session_id=test_session_id,
        category="tool",
        fact="Uses uv for package management",
        embedding=embedding
    )

    exists = client.projectFactExists(test_project, embedding, threshold=0.9)
    assert exists

    random.seed(999)
    different_embedding = [random.uniform(-1, 1) for _ in range(384)]
    exists_different = client.projectFactExists(test_project, different_embedding, threshold=0.9)
    assert not exists_different


@pytest.mark.integration
def test_metrics_include_project_facts(client, test_project, test_session_id):
    """Test that getAllMetrics includes project facts count."""
    from datetime import datetime

    client.createSession(
        session_id=test_session_id,
        project=test_project,
        started_at=datetime.now().isoformat()
    )

    metrics = client.getAllMetrics(test_project)
    assert "total_project_facts" in metrics
