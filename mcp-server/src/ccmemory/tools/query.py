"""MCP tools for querying the context graph."""

import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..graph import getClient
from ..embeddings import getEmbedding


def registerQueryTools(mcp: FastMCP):
    """Register all query tools with the MCP server."""

    @mcp.tool()
    async def queryContext(
        limit: int = 20,
        include_team: bool = True
    ) -> dict:
        """Get recent context for the current project.

        Args:
            limit: Maximum number of items to return
            include_team: Whether to include curated team decisions
        """
        client = getClient()
        project = os.path.basename(os.getcwd())
        results = client.queryRecent(project, limit=limit, include_team=include_team)

        formatted = []
        for item in results:
            node = item.get("n", {})
            rel_type = item.get("rel_type", "")
            formatted.append({
                "type": rel_type,
                "data": dict(node),
                "session_time": str(item.get("session_time", ""))
            })

        return {"project": project, "context": formatted}

    @mcp.tool()
    async def searchPrecedent(
        query: str,
        limit: int = 10,
        include_team: bool = True
    ) -> dict:
        """Full-text search across all context types.

        Args:
            query: Search query
            limit: Maximum results per category
            include_team: Whether to include curated team decisions
        """
        client = getClient()
        project = os.path.basename(os.getcwd())
        results = client.searchPrecedent(query, project, limit=limit, include_team=include_team)

        return {"project": project, "query": query, "results": results}

    @mcp.tool()
    async def searchSemantic(
        query: str,
        limit: int = 10,
        include_team: bool = True
    ) -> dict:
        """Semantic similarity search across decisions, corrections, and insights.

        Args:
            query: Natural language query
            limit: Maximum results per category
            include_team: Whether to include curated team decisions
        """
        client = getClient()
        project = os.path.basename(os.getcwd())

        embedding = getEmbedding(query)
        results = client.searchSemantic(embedding, project, limit=limit, include_team=include_team)

        formatted = {}
        for category, items in results.items():
            formatted[category] = [
                {"data": item[0], "score": item[1]}
                for item in items
            ]

        return {"project": project, "query": query, "results": formatted}

    @mcp.tool()
    async def queryByTopic(
        topic: str,
        limit: int = 20
    ) -> dict:
        """Get all context related to a specific topic.

        Args:
            topic: Topic to query (e.g., "auth", "database", "deployment")
            limit: Maximum results
        """
        client = getClient()
        project = os.path.basename(os.getcwd())

        # Combine full-text and semantic search
        text_results = client.searchPrecedent(topic, project, limit=limit)

        embedding = getEmbedding(topic)
        semantic_results = client.searchSemantic(embedding, project, limit=limit)

        return {
            "project": project,
            "topic": topic,
            "text_matches": text_results,
            "semantic_matches": {
                category: [{"data": item[0], "score": item[1]} for item in items]
                for category, items in semantic_results.items()
            }
        }

    @mcp.tool()
    async def traceDecision(
        decision_id: str
    ) -> dict:
        """Trace the full context around a decision.

        Args:
            decision_id: ID of the decision to trace
        """
        client = getClient()
        driver = client.driver

        with driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {id: $decision_id})
                OPTIONAL MATCH (s:Session)-[:DECIDED]->(d)
                OPTIONAL MATCH (d)-[:CITES]->(cited:Decision)
                OPTIONAL MATCH (d)-[:SUPERSEDES]->(superseded:Decision)
                OPTIONAL MATCH (superseding:Decision)-[:SUPERSEDES]->(d)
                OPTIONAL MATCH (s)-[:CORRECTED]->(c:Correction)
                OPTIONAL MATCH (s)-[:EXCEPTED]->(e:Exception)
                RETURN d, s, collect(DISTINCT cited) as cited,
                       collect(DISTINCT superseded) as superseded,
                       collect(DISTINCT superseding) as superseding,
                       collect(DISTINCT c) as corrections,
                       collect(DISTINCT e) as exceptions
                """,
                decision_id=decision_id
            )
            record = result.single()

            if not record:
                return {"error": f"Decision {decision_id} not found"}

            return {
                "decision": dict(record["d"]) if record["d"] else None,
                "session": dict(record["s"]) if record["s"] else None,
                "cites": [dict(n) for n in record["cited"] if n],
                "supersedes": [dict(n) for n in record["superseded"] if n],
                "superseded_by": [dict(n) for n in record["superseding"] if n],
                "session_corrections": [dict(n) for n in record["corrections"] if n],
                "session_exceptions": [dict(n) for n in record["exceptions"] if n],
            }

    @mcp.tool()
    async def queryStaleDecisions(
        days: int = 30
    ) -> dict:
        """Find developmental decisions that may need review.

        Args:
            days: Consider decisions older than this many days as stale
        """
        client = getClient()
        project = os.path.basename(os.getcwd())
        results = client.queryStaleDecisions(project, days=days)

        return {
            "project": project,
            "threshold_days": days,
            "stale_decisions": results
        }

    @mcp.tool()
    async def queryFailedApproaches(
        limit: int = 10
    ) -> dict:
        """Get recent failed approaches to avoid repeating mistakes.

        Args:
            limit: Maximum results
        """
        client = getClient()
        project = os.path.basename(os.getcwd())
        results = client.queryFailedApproaches(project, limit=limit)

        return {
            "project": project,
            "failed_approaches": results
        }

    @mcp.tool()
    async def promoteDecisions(
        branch: Optional[str] = None
    ) -> dict:
        """Promote developmental decisions to curated status.

        Args:
            branch: Only promote decisions from this branch (optional)
        """
        client = getClient()
        project = os.path.basename(os.getcwd())
        client.promoteDecisions(project, branch=branch)

        return {
            "project": project,
            "branch": branch,
            "status": "promoted"
        }

    @mcp.tool()
    async def getMetrics() -> dict:
        """Get all context graph metrics for the current project."""
        client = getClient()
        project = os.path.basename(os.getcwd())
        return client.getAllMetrics(project)
