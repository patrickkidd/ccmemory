import os
import uuid
import json
import logging
import time
from pathlib import Path
from typing import Optional
from neo4j import GraphDatabase

logger = logging.getLogger("ccmemory.graph")

# Suppress Neo4j notifications about missing relationship types
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)


class GraphClient:
    def __init__(self, init_schema: bool = False):
        uri = os.getenv("CCMEMORY_NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("CCMEMORY_NEO4J_USER", "neo4j")
        password = os.getenv("CCMEMORY_NEO4J_PASSWORD", "ccmemory")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.user_id = os.getenv("CCMEMORY_USER_ID")
        if init_schema:
            self.init_schema()

    def init_schema(self):
        """Initialize Neo4j schema from init.cypher."""
        cypher_paths = [
            Path("/app/init.cypher"),
            Path(__file__).parent.parent.parent / "init.cypher",
        ]
        for path in cypher_paths:
            if path.exists():
                cypher = path.read_text()
                for stmt in cypher.split(";"):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith("//"):
                        with self.driver.session() as session:
                            session.run(stmt)
                logging.info("Schema initialized from %s", path)
                return
        logging.warning("init.cypher not found")

    def close(self):
        self.driver.close()

    # === Session Management ===

    def createSession(
        self,
        session_id: str,
        project: str,
        started_at: str,
        branch: Optional[str] = None,
    ):
        logger.debug(f"createSession(project={project}, id={session_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MERGE (s:Session {id: $id})
                SET s.project = $project,
                    s.started_at = datetime($started_at),
                    s.user_id = $user_id,
                    s.branch = $branch
                """,
                id=session_id,
                project=project,
                started_at=started_at,
                user_id=self.user_id,
                branch=branch,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Session id={session_id[:12]}... ({duration}ms)")

    def endSession(self, session_id: str, transcript: str, summary: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $id})
                SET s.ended_at = datetime(),
                    s.transcript = $transcript,
                    s.summary = $summary
                """,
                id=session_id,
                transcript=transcript,
                summary=summary,
            )

    def sessionExists(self, session_id: str) -> bool:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (s:Session {id: $id}) RETURN count(s) > 0 as exists",
                id=session_id,
            )
            return result.single()["exists"]

    def filterExistingSessions(self, session_ids: list[str]) -> set[str]:
        """Return set of session_ids that already exist in the database."""
        if not session_ids:
            return set()
        with self.driver.session() as session:
            result = session.run(
                "UNWIND $ids AS id MATCH (s:Session {id: id}) RETURN s.id as id",
                ids=session_ids,
            )
            return {r["id"] for r in result}

    def decisionExists(self, project: str, description: str) -> bool:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {project: $project, description: $description})
                RETURN count(d) > 0 as exists
                """,
                project=project,
                description=description,
            )
            return result.single()["exists"]

    def referenceFileExists(self, project: str, source_file: str) -> bool:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:ReferenceChunk {project: $project, source_file: $source_file})
                RETURN count(c) > 0 as exists
                """,
                project=project,
                source_file=source_file,
            )
            return result.single()["exists"]

    # === Domain 1: Record Functions ===

    def createDecision(
        self,
        decision_id: str,
        session_id: str,
        description: str,
        embedding: list,
        **kwargs,
    ):
        logger.debug(f"createDecision(id={decision_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (d:Decision {id: $decision_id})
                SET d.description = $description,
                    d.timestamp = datetime(),
                    d.project = s.project,
                    d.user_id = s.user_id,
                    d.status = 'developmental',
                    d.embedding = $embedding
                SET d += $props
                CREATE (s)-[:DECIDED]->(d)
                """,
                session_id=session_id,
                decision_id=decision_id,
                description=description,
                embedding=embedding,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Decision id={decision_id[:12]}... ({duration}ms)")

    def createCorrection(
        self,
        correction_id: str,
        session_id: str,
        wrong_belief: str,
        right_belief: str,
        embedding: list,
        **kwargs,
    ):
        logger.debug(f"createCorrection(id={correction_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (c:Correction {id: $correction_id})
                SET c.wrong_belief = $wrong_belief,
                    c.right_belief = $right_belief,
                    c.timestamp = datetime(),
                    c.project = s.project,
                    c.user_id = s.user_id,
                    c.embedding = $embedding
                SET c += $props
                CREATE (s)-[:CORRECTED]->(c)
                """,
                session_id=session_id,
                correction_id=correction_id,
                wrong_belief=wrong_belief,
                right_belief=right_belief,
                embedding=embedding,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Correction id={correction_id[:12]}... ({duration}ms)")

    def createException(
        self,
        exception_id: str,
        session_id: str,
        rule_broken: str,
        justification: str,
        embedding: list,
        **kwargs,
    ):
        logger.debug(f"createException(id={exception_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (e:Exception {id: $exception_id})
                SET e.rule_broken = $rule_broken,
                    e.justification = $justification,
                    e.timestamp = datetime(),
                    e.project = s.project,
                    e.user_id = s.user_id,
                    e.embedding = $embedding
                SET e += $props
                CREATE (s)-[:EXCEPTED]->(e)
                """,
                session_id=session_id,
                exception_id=exception_id,
                rule_broken=rule_broken,
                justification=justification,
                embedding=embedding,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Exception id={exception_id[:12]}... ({duration}ms)")

    def createInsight(
        self,
        insight_id: str,
        session_id: str,
        category: str,
        summary: str,
        embedding: list,
        **kwargs,
    ):
        logger.debug(f"createInsight(id={insight_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (i:Insight {id: $insight_id})
                SET i.category = $category,
                    i.summary = $summary,
                    i.timestamp = datetime(),
                    i.project = s.project,
                    i.user_id = s.user_id,
                    i.embedding = $embedding
                SET i += $props
                CREATE (s)-[:REALIZED]->(i)
                """,
                session_id=session_id,
                insight_id=insight_id,
                category=category,
                summary=summary,
                embedding=embedding,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Insight id={insight_id[:12]}... ({duration}ms)")

    def createQuestion(
        self, question_id: str, session_id: str, question: str, answer: str, **kwargs
    ):
        logger.debug(f"createQuestion(id={question_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (q:Question {id: $question_id})
                SET q.question = $question,
                    q.answer = $answer,
                    q.timestamp = datetime(),
                    q.project = s.project,
                    q.user_id = s.user_id
                SET q += $props
                CREATE (s)-[:ASKED]->(q)
                """,
                session_id=session_id,
                question_id=question_id,
                question=question,
                answer=answer,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Question id={question_id[:12]}... ({duration}ms)")

    def createFailedApproach(
        self,
        fa_id: str,
        session_id: str,
        approach: str,
        outcome: str,
        lesson: str,
        **kwargs,
    ):
        logger.debug(f"createFailedApproach(id={fa_id[:12]}...)")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (f:FailedApproach {id: $fa_id})
                SET f.approach = $approach,
                    f.outcome = $outcome,
                    f.lesson = $lesson,
                    f.timestamp = datetime(),
                    f.project = s.project,
                    f.user_id = s.user_id
                SET f += $props
                CREATE (s)-[:TRIED]->(f)
                """,
                session_id=session_id,
                fa_id=fa_id,
                approach=approach,
                outcome=outcome,
                lesson=lesson,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created FailedApproach id={fa_id[:12]}... ({duration}ms)")

    def createReference(
        self, ref_id: str, session_id: str, ref_type: str, uri: str, **kwargs
    ):
        logger.debug(f"createReference(id={ref_id[:12]}..., type={ref_type})")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (r:Reference {id: $ref_id})
                SET r.type = $ref_type,
                    r.uri = $uri,
                    r.timestamp = datetime(),
                    r.project = s.project,
                    r.user_id = s.user_id
                SET r += $props
                CREATE (s)-[:REFERENCED]->(r)
                """,
                session_id=session_id,
                ref_id=ref_id,
                ref_type=ref_type,
                uri=uri,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(f"Created Reference id={ref_id[:12]}... ({duration}ms)")

    # === Domain 1: Query Functions ===

    def queryRecent(self, project: str, limit: int = 20, include_team: bool = True):
        """Get recent context for a project."""
        logger.debug(f"queryRecent(project={project}, limit={limit})")
        start = time.time()
        with self.driver.session() as session:
            if include_team and self.user_id:
                visibility = "(n.status = 'curated' OR n.user_id = $user_id)"
            else:
                visibility = "n.user_id = $user_id" if self.user_id else "true"

            result = session.run(
                f"""
                MATCH (s:Session {{project: $project}})-[r]->(n)
                WHERE {visibility}
                RETURN n, type(r) as rel_type, s.started_at as session_time
                ORDER BY n.timestamp DESC
                LIMIT $limit
                """,
                project=project,
                user_id=self.user_id,
                limit=limit,
            )
            records = [dict(record) for record in result]
        duration = int((time.time() - start) * 1000)
        logger.debug(f"queryRecent returned {len(records)} items ({duration}ms)")
        return records

    def searchPrecedent(
        self, query: str, project: str, limit: int = 10, include_team: bool = True
    ):
        """Full-text search across all node types with team visibility filtering."""
        with self.driver.session() as session:
            results = {}
            indexes = [
                ("decision_search", "decisions"),
                ("correction_search", "corrections"),
                ("insight_search", "insights"),
                ("question_search", "questions"),
                ("failedapproach_search", "failed_approaches"),
            ]

            if include_team and self.user_id:
                visibility = "(node.status = 'curated' OR node.user_id = $user_id)"
            else:
                visibility = "node.user_id = $user_id" if self.user_id else "true"

            for index, key in indexes:
                result = session.run(
                    f"""
                    CALL db.index.fulltext.queryNodes("{index}", $search_query)
                    YIELD node, score
                    WHERE node.project = $project AND {visibility}
                    RETURN node, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    search_query=query,
                    project=project,
                    user_id=self.user_id,
                    limit=limit,
                )
                results[key] = [(dict(r["node"]), r["score"]) for r in result]
            return results

    def searchSemantic(
        self, embedding: list, project: str, limit: int = 10, include_team: bool = True
    ):
        """Vector similarity search across Domain 1 with team visibility filtering."""
        with self.driver.session() as session:
            results = {}
            indexes = [
                ("decision_embedding", "decisions"),
                ("correction_embedding", "corrections"),
                ("insight_embedding", "insights"),
            ]

            if include_team and self.user_id:
                visibility = "(node.status = 'curated' OR node.user_id = $user_id)"
            else:
                visibility = "node.user_id = $user_id" if self.user_id else "true"

            for index, key in indexes:
                result = session.run(
                    f"""
                    CALL db.index.vector.queryNodes('{index}', $limit, $embedding)
                    YIELD node, score
                    WHERE node.project = $project AND {visibility}
                    RETURN node, score
                    """,
                    embedding=embedding,
                    project=project,
                    user_id=self.user_id,
                    limit=limit,
                )
                results[key] = [(dict(r["node"]), r["score"]) for r in result]
            return results

    def queryStaleDecisions(self, project: str, days: int = 30):
        """Find developmental decisions that may need review or promotion."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                WHERE d.status = 'developmental'
                  AND d.timestamp < datetime() - duration({days: $days})
                RETURN d
                ORDER BY d.timestamp DESC
                """,
                project=project,
                days=days,
            )
            return [dict(record["d"]) for record in result]

    def queryFailedApproaches(self, project: str, limit: int = 10):
        """Get recent failed approaches."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (f:FailedApproach {project: $project})
                RETURN f
                ORDER BY f.timestamp DESC
                LIMIT $limit
                """,
                project=project,
                limit=limit,
            )
            return [dict(record["f"]) for record in result]

    # === Domain 2: Chunk Index ===

    def indexChunk(
        self,
        chunk_id: str,
        project: str,
        source_file: str,
        section: str,
        content: str,
        embedding: list,
    ):
        """Index a markdown chunk for semantic search."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (ch:Chunk {id: $chunk_id})
                SET ch.project = $project,
                    ch.source_file = $source_file,
                    ch.section = $section,
                    ch.content = $content,
                    ch.embedding = $embedding,
                    ch.last_indexed = datetime()
                """,
                chunk_id=chunk_id,
                project=project,
                source_file=source_file,
                section=section,
                content=content,
                embedding=embedding,
            )

    def searchReference(self, embedding: list, project: str, limit: int = 5):
        """Semantic search over Domain 2 chunks."""
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.vector.queryNodes('chunk_embedding', $limit, $embedding)
                YIELD node, score
                WHERE node.project = $project
                RETURN node, score
                """,
                embedding=embedding,
                project=project,
                limit=limit,
            )
            return [(dict(r["node"]), r["score"]) for r in result]

    def clearChunks(self, project: str, source_file: Optional[str] = None):
        """Clear chunks for re-indexing."""
        with self.driver.session() as session:
            if source_file:
                session.run(
                    "MATCH (ch:Chunk {project: $project, source_file: $source_file}) DELETE ch",
                    project=project,
                    source_file=source_file,
                )
            else:
                session.run(
                    "MATCH (ch:Chunk {project: $project}) DELETE ch", project=project
                )

    # === Promotion ===

    def promoteDecisions(self, project: str, branch: Optional[str] = None):
        """Promote developmental decisions to curated."""
        with self.driver.session() as session:
            query = """
                MATCH (d:Decision {project: $project, status: 'developmental'})
                WHERE d.user_id = $user_id
            """
            if branch:
                query += " AND d.branch = $branch"
            query += " SET d.status = 'curated', d.promoted_at = datetime()"
            session.run(query, project=project, user_id=self.user_id, branch=branch)

    # === Telemetry ===

    def recordTelemetry(self, event_type: str, project: str, data: dict):
        """Record a telemetry event."""
        with self.driver.session() as session:
            session.run(
                """
                CREATE (t:TelemetryEvent {
                    id: $id,
                    event_type: $event_type,
                    project: $project,
                    user_id: $user_id,
                    timestamp: datetime(),
                    data_json: $data_json,
                    count: $count,
                    duration_ms: $duration_ms
                })
                """,
                id=f"telem-{uuid.uuid4().hex[:12]}",
                event_type=event_type,
                project=project,
                user_id=self.user_id,
                data_json=json.dumps(data),
                count=data.get("count"),
                duration_ms=data.get("duration_ms"),
            )

    # === Metrics ===

    def calculateCoefficient(self, project: str) -> float:
        """Calculate cognitive coefficient from observable metrics."""
        curated = self._countNodes("Decision", project, status="curated")
        reuse_rate = self.calculateDecisionReuseRate(project)
        reexplanation = self.calculateReexplanationRate(project)
        correction_improvement = max(0.0, min(1.0, 1.0 - reexplanation))

        coefficient = (
            1.0 + (curated * 0.02) + (correction_improvement * 0.5) + (reuse_rate * 1.0)
        )
        return min(4.0, coefficient)

    def calculateReexplanationRate(self, project: str) -> float:
        """Calculate re-explanation rate (corrections as proxy)."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Correction {project: $project})
                RETURN count(c) as corrections
                """,
                project=project,
            )
            corrections = result.single()["corrections"]

            result = session.run(
                """
                MATCH (s:Session {project: $project})
                RETURN count(s) as sessions
                """,
                project=project,
            )
            sessions = result.single()["sessions"]

            if sessions == 0:
                return 0.0
            return corrections / sessions

    def calculateDecisionReuseRate(self, project: str) -> float:
        """Calculate decision reuse rate."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                OPTIONAL MATCH (d)-[:CITES|SUPERSEDES]->(prior:Decision)
                WITH count(d) as total, count(prior) as with_precedent
                RETURN CASE WHEN total = 0 THEN 0.0
                       ELSE with_precedent * 1.0 / total END as rate
                """,
                project=project,
            )
            return result.single()["rate"]

    def calculateGraphDensity(self, project: str) -> float:
        """Calculate context graph density."""
        with self.driver.session() as session:
            result = session.run(
                """
                OPTIONAL MATCH (n {project: $project})
                WITH count(n) as nodes
                OPTIONAL MATCH ({project: $project})-[r]->({project: $project})
                WITH nodes, count(r) as edges
                RETURN CASE WHEN nodes = 0 THEN 0.0
                       ELSE edges * 1.0 / nodes END as density
                """,
                project=project,
            )
            record = result.single()
            return record["density"] if record else 0.0

    def getAllMetrics(self, project: str) -> dict:
        """Get all metrics for dashboard."""
        return {
            "cognitive_coefficient": self.calculateCoefficient(project),
            "reexplanation_rate": self.calculateReexplanationRate(project),
            "decision_reuse_rate": self.calculateDecisionReuseRate(project),
            "graph_density": self.calculateGraphDensity(project),
            "total_decisions": self._countNodes("Decision", project),
            "total_corrections": self._countNodes("Correction", project),
            "total_sessions": self._countNodes("Session", project),
            "total_insights": self._countNodes("Insight", project),
            "total_failed_approaches": self._countNodes("FailedApproach", project),
        }

    def _countNodes(self, label: str, project: str, status: str = None) -> int:
        with self.driver.session() as session:
            if status:
                result = session.run(
                    f"MATCH (n:{label} {{project: $project, status: $status}}) RETURN count(n) as count",
                    project=project,
                    status=status,
                )
            else:
                result = session.run(
                    f"MATCH (n:{label} {{project: $project}}) RETURN count(n) as count",
                    project=project,
                )
            return result.single()["count"]


# Singleton
_client = None


def getClient() -> GraphClient:
    global _client
    if _client is None:
        _client = GraphClient()
    return _client
