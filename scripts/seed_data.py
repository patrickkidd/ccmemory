#!/usr/bin/env python
"""Seed synthetic data for E2E testing."""

import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from ccmemory.graph import getClient
from ccmemory.embeddings import EMBEDDING_DIMS

PROJECT = "ccmemory"


def zero_embedding():
    """Return zero embedding for testing without Voyage API."""
    return [0.0] * EMBEDDING_DIMS


def seed():
    client = getClient()
    now = datetime.now()

    # Create sessions
    session_ids = []
    for i in range(5):
        session_id = f"session-{i+1}"
        session_ids.append(session_id)
        client.createSession(
            session_id=session_id,
            project=PROJECT,
            started_at=(now - timedelta(days=i)).isoformat(),
            branch=f"feature/test-{i+1}" if i < 3 else "main"
        )
        print(f"Created session: {session_id}")

    # Create decisions
    decisions = [
        {
            "description": "Use Neo4j for graph storage instead of PostgreSQL",
            "rationale": "Graph queries are more natural for relationship-heavy data",
            "options_considered": ["PostgreSQL with ltree", "Neo4j", "DGraph"],
            "revisit_trigger": "If query performance degrades below 100ms",
            "topic": "database",
            "session_id": session_ids[0],
            "status": "curated"
        },
        {
            "description": "Use Voyage AI for embeddings instead of OpenAI",
            "rationale": "Better semantic similarity for code and technical content",
            "options_considered": ["OpenAI ada-002", "Voyage-3", "Cohere embed-v3"],
            "topic": "embeddings",
            "session_id": session_ids[0],
            "status": "curated"
        },
        {
            "description": "Implement LLM-based detection for context capture",
            "rationale": "Regex-based detection misses nuanced corrections",
            "topic": "detection",
            "session_id": session_ids[1],
            "status": "developmental"
        },
        {
            "description": "Use Flask for dashboard instead of FastAPI",
            "rationale": "Simpler for server-rendered templates",
            "options_considered": ["FastAPI", "Flask", "Django"],
            "topic": "dashboard",
            "session_id": session_ids[2],
            "status": "developmental"
        },
        {
            "description": "Store embeddings directly in Neo4j vector index",
            "rationale": "Avoid separate vector database dependency",
            "topic": "embeddings",
            "session_id": session_ids[3],
            "status": "developmental",
            "revisit_trigger": "If Neo4j vector search performance is inadequate"
        },
    ]

    for d in decisions:
        client.createDecision(
            decision_id=str(uuid.uuid4()),
            session_id=d["session_id"],
            description=d["description"],
            embedding=zero_embedding(),
            rationale=d.get("rationale"),
            options_considered=d.get("options_considered"),
            revisit_trigger=d.get("revisit_trigger"),
            topic=d.get("topic"),
            status=d.get("status", "developmental"),
        )
        print(f"Created decision: {d['description'][:50]}...")

    # Create corrections
    corrections = [
        {
            "wrong_belief": "The session hook runs after each message",
            "right_belief": "Session hooks only run at session start and end",
            "severity": "high",
            "topic": "hooks",
            "session_id": session_ids[0]
        },
        {
            "wrong_belief": "Neo4j requires a separate APOC installation",
            "right_belief": "APOC can be enabled via NEO4J_PLUGINS environment variable",
            "severity": "medium",
            "topic": "database",
            "session_id": session_ids[1]
        },
        {
            "wrong_belief": "MCP tools must return strings",
            "right_belief": "MCP tools can return structured dicts that get serialized",
            "severity": "low",
            "topic": "mcp",
            "session_id": session_ids[2]
        },
    ]

    for c in corrections:
        client.createCorrection(
            correction_id=str(uuid.uuid4()),
            session_id=c["session_id"],
            wrong_belief=c["wrong_belief"],
            right_belief=c["right_belief"],
            embedding=zero_embedding(),
            severity=c.get("severity", "medium"),
            topic=c.get("topic"),
        )
        print(f"Created correction: {c['wrong_belief'][:40]}...")

    # Create insights
    insights = [
        {
            "summary": "Graph density correlates with cognitive coefficient",
            "details": "Projects with more decision interconnections show higher reuse rates",
            "topic": "metrics",
            "session_id": session_ids[0]
        },
        {
            "summary": "Corrections are highest-value captures",
            "details": "User corrections represent ground truth that should never be forgotten",
            "topic": "learning",
            "session_id": session_ids[1]
        },
        {
            "summary": "Session context injection improves first-response quality",
            "details": "Injecting recent context at session start reduces re-explanation requests by 40%",
            "topic": "effectiveness",
            "session_id": session_ids[2]
        },
    ]

    for i in insights:
        client.createInsight(
            insight_id=str(uuid.uuid4()),
            session_id=i["session_id"],
            category=i.get("topic", "general"),
            summary=i["summary"],
            embedding=zero_embedding(),
            details=i.get("details"),
        )
        print(f"Created insight: {i['summary'][:50]}...")

    # Create failed approaches
    failed = [
        {
            "approach": "Using regex to detect user corrections",
            "why_failed": "Too many false positives with phrases like 'no, wait'",
            "alternative": "LLM-based semantic analysis",
            "topic": "detection",
            "session_id": session_ids[1]
        },
        {
            "approach": "Storing embeddings in a separate Pinecone index",
            "why_failed": "Added operational complexity without clear benefit",
            "alternative": "Use Neo4j native vector index",
            "topic": "architecture",
            "session_id": session_ids[2]
        },
    ]

    for f in failed:
        client.createFailedApproach(
            fa_id=str(uuid.uuid4()),
            session_id=f["session_id"],
            approach=f["approach"],
            outcome=f["why_failed"],
            lesson=f.get("alternative", "Try a different approach"),
        )
        print(f"Created failed approach: {f['approach'][:40]}...")

    # Create exceptions
    exceptions = [
        {
            "rule": "Always use vector search for similarity",
            "exception": "Skip embeddings for exact topic matches",
            "rationale": "Faster and more precise when topic is specified",
            "topic": "search",
            "session_id": session_ids[0]
        },
    ]

    for e in exceptions:
        client.createException(
            exception_id=str(uuid.uuid4()),
            session_id=e["session_id"],
            rule_broken=e["rule"],
            justification=e["exception"] + ": " + e.get("rationale", ""),
            embedding=zero_embedding(),
        )
        print(f"Created exception: {e['exception'][:40]}...")

    # Record some telemetry
    client.recordTelemetry(
        event_type="session_metrics",
        project=PROJECT,
        data={
            "session_id": session_ids[0],
            "reexplanations": 2,
            "decision_reuses": 5,
            "corrections_used": 3,
            "total_messages": 25
        }
    )
    print("Recorded telemetry")

    # Get and display metrics
    metrics = client.getAllMetrics(PROJECT)
    print("\n=== Metrics ===")
    print(f"Cognitive Coefficient: {metrics['cognitive_coefficient']:.2f}x")
    print(f"Total Decisions: {metrics['total_decisions']}")
    print(f"Total Corrections: {metrics['total_corrections']}")
    print(f"Total Sessions: {metrics['total_sessions']}")
    print(f"Total Insights: {metrics['total_insights']}")
    print(f"Graph Density: {metrics['graph_density']:.2f}")

    print("\nSynthetic data seeded successfully!")


if __name__ == "__main__":
    seed()
