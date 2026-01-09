"""MCP tools for querying the context graph."""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..graph import getClient
from ..embeddings import getEmbedding
from ..reranker import rerank
from ..context import getCurrentProject
from .logging import logTool


def _getProject() -> str:
    """Get current project or raise error."""
    project = getCurrentProject()
    if not project:
        raise ValueError("No active session. Start a Claude Code session first.")
    return project


def registerQueryTools(mcp: FastMCP):
    """Register all query tools with the MCP server."""

    @mcp.tool()
    @logTool
    async def queryContext(limit: int = 20, include_team: bool = True) -> dict:
        """Get recent context for the current project.

        Args:
            limit: Maximum number of items to return
            include_team: Whether to include curated team decisions
        """
        client = getClient()
        project = _getProject()
        results = client.queryRecent(project, limit=limit, include_team=include_team)

        formatted = []
        for item in results:
            node = item.get("n", {})
            rel_type = item.get("rel_type", "")
            formatted.append(
                {
                    "type": rel_type,
                    "data": dict(node),
                    "session_time": str(item.get("session_time", "")),
                }
            )

        return {"project": project, "context": formatted}

    @mcp.tool()
    @logTool
    async def searchPrecedent(
        query: str, limit: int = 10, include_team: bool = True
    ) -> dict:
        """Full-text search across all context types.

        Args:
            query: Search query
            limit: Maximum results per category
            include_team: Whether to include curated team decisions
        """
        client = getClient()
        project = _getProject()
        results = client.searchPrecedent(
            query, project, limit=limit, include_team=include_team
        )

        return {"project": project, "query": query, "results": results}

    @mcp.tool()
    @logTool
    async def searchSemantic(
        query: str, limit: int = 10, include_team: bool = True
    ) -> dict:
        """Semantic similarity search across decisions, corrections, and insights.

        Uses local embeddings for candidate retrieval, then Claude for reranking.

        Args:
            query: Natural language query
            limit: Maximum results to return
            include_team: Whether to include curated team decisions
        """
        client = getClient()
        project = _getProject()

        embedding = getEmbedding(query)
        raw_limit = min(limit * 2, 20)
        results = client.searchSemantic(
            embedding, project, limit=raw_limit, include_team=include_team
        )

        candidates = []
        for category, items in results.items():
            for item in items:
                candidates.append(
                    {"data": item[0], "score": item[1], "category": category}
                )

        candidates.sort(key=lambda x: x["score"], reverse=True)

        reranked = await rerank(query, candidates, limit=limit)

        formatted = {}
        for item in reranked:
            cat = item.get("category", "unknown")
            if cat not in formatted:
                formatted[cat] = []
            formatted[cat].append({"data": item["data"], "score": item["score"]})

        return {"project": project, "query": query, "results": formatted}

    @mcp.tool()
    @logTool
    async def queryByTopic(topic: str, limit: int = 20) -> dict:
        """Get all context related to a specific topic.

        Args:
            topic: Topic to query (e.g., "auth", "database", "deployment")
            limit: Maximum results
        """
        client = getClient()
        project = _getProject()

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
            },
        }

    @mcp.tool()
    @logTool
    async def traceDecision(decision_id: str) -> dict:
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
                OPTIONAL MATCH (d)-[:CITES]->(cited:Decision)
                OPTIONAL MATCH (d)-[:SUPERSEDES]->(superseded:Decision)
                OPTIONAL MATCH (superseding:Decision)-[:SUPERSEDES]->(d)
                OPTIONAL MATCH (d)-[:DEPENDS_ON]->(depends:Decision)
                OPTIONAL MATCH (d)-[:CONSTRAINS]->(constrains:Decision)
                OPTIONAL MATCH (d)-[:CONFLICTS_WITH]->(conflicts:Decision)
                RETURN d,
                       collect(DISTINCT cited) as cited,
                       collect(DISTINCT superseded) as superseded,
                       collect(DISTINCT superseding) as superseding,
                       collect(DISTINCT depends) as depends_on,
                       collect(DISTINCT constrains) as constrains,
                       collect(DISTINCT conflicts) as conflicts_with
                """,
                decision_id=decision_id,
            )
            record = result.single()

            if not record:
                return {"error": f"Decision {decision_id} not found"}

            return {
                "decision": dict(record["d"]) if record["d"] else None,
                "cites": [dict(n) for n in record["cited"] if n],
                "supersedes": [dict(n) for n in record["superseded"] if n],
                "superseded_by": [dict(n) for n in record["superseding"] if n],
                "depends_on": [dict(n) for n in record["depends_on"] if n],
                "constrains": [dict(n) for n in record["constrains"] if n],
                "conflicts_with": [dict(n) for n in record["conflicts_with"] if n],
            }

    @mcp.tool()
    @logTool
    async def queryStaleDecisions(days: int = 30) -> dict:
        """Find developmental decisions that may need review.

        Args:
            days: Consider decisions older than this many days as stale
        """
        client = getClient()
        project = _getProject()
        results = client.queryStaleDecisions(project, days=days)

        return {"project": project, "threshold_days": days, "stale_decisions": results}

    @mcp.tool()
    @logTool
    async def queryFailedApproaches(limit: int = 10) -> dict:
        """Get recent failed approaches to avoid repeating mistakes.

        Args:
            limit: Maximum results
        """
        client = getClient()
        project = _getProject()
        results = client.queryFailedApproaches(project, limit=limit)

        return {"project": project, "failed_approaches": results}

    @mcp.tool()
    @logTool
    async def promoteDecisions(branch: Optional[str] = None) -> dict:
        """Promote developmental decisions to curated status.

        Args:
            branch: Only promote decisions from this branch (optional)
        """
        client = getClient()
        project = _getProject()
        client.promoteDecisions(project, branch=branch)

        return {"project": project, "branch": branch, "status": "promoted"}

    @mcp.tool()
    @logTool
    async def getMetrics() -> dict:
        """Get all context graph metrics for the current project."""
        client = getClient()
        project = _getProject()
        return client.getAllMetrics(project)

    @mcp.tool()
    @logTool
    async def queryOpenQuestions(limit: int = 10) -> dict:
        """Get unanswered questions from the context graph.

        Args:
            limit: Maximum results
        """
        client = getClient()
        project = _getProject()
        results = client.queryOpenQuestions(project, limit=limit)
        return {"project": project, "open_questions": results}

    @mcp.tool()
    @logTool
    async def queryPatterns() -> dict:
        """Get detected patterns from the context graph.

        Returns exception clusters, supersession chains, and correction hotspots.
        """
        client = getClient()
        project = _getProject()

        return {
            "project": project,
            "exception_clusters": client.queryExceptionClusters(project),
            "supersession_chains": client.querySupersessionChains(project),
            "correction_hotspots": client.queryCorrectionHotspots(project),
        }
