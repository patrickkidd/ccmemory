"""Neo4j graph client for ccmemory.

Per doc/clarifications/1-DAG-with-CROSS-REFS.md:
- No Session nodes as organizing principle
- All nodes have timestamp + project directly
- Cross-references via SUPERSEDES, CITES, etc.
"""

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
            self.initSchema()

    def initSchema(self):
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

    # === Existence Checks ===

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

    def projectFactExists(
        self, project: str, embedding: list, threshold: float = 0.9
    ) -> bool:
        """Check if a semantically similar fact already exists."""
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.vector.queryNodes('projectfact_embedding', 50, $embedding)
                YIELD node, score
                WHERE node.project = $project AND score >= $threshold
                RETURN node, score
                LIMIT 1
                """,
                embedding=embedding,
                project=project,
                threshold=threshold,
            )
            return result.single() is not None

    def _isDuplicate(
        self, index_name: str, project: str, embedding: list, threshold: float = 0.9
    ) -> dict | None:
        """Check if semantically similar node exists. Returns match info or None."""
        if not embedding:
            return None
        with self.driver.session() as session:
            result = session.run(
                f"""
                CALL db.index.vector.queryNodes('{index_name}', 3, $embedding)
                YIELD node, score
                WHERE node.project = $project AND score >= $threshold
                RETURN node.id as id, score
                ORDER BY score DESC
                LIMIT 1
                """,
                embedding=embedding,
                project=project,
                threshold=threshold,
            )
            record = result.single()
            if record:
                return {"id": record["id"], "score": record["score"]}
            return None

    # === Domain 1: Record Functions ===
    # All methods take project directly (no session dependency)

    def createDecision(
        self,
        decision_id: str,
        project: str,
        description: str,
        embedding: list,
        topics: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Create a decision with deduplication and auto-linking.

        Returns dict with 'action': 'created', 'skipped', or 'superseded'
        """
        logger.debug(f"createDecision(id={decision_id[:12]}..., project={project})")
        start = time.time()

        with self.driver.session() as session:
            # Check for semantic duplicates
            if embedding:
                dup_result = session.run(
                    """
                    CALL db.index.vector.queryNodes('decision_embedding', 3, $embedding)
                    YIELD node, score
                    WHERE node.project = $project
                    RETURN node.id as id, node.description as description, score
                    ORDER BY score DESC
                    LIMIT 1
                    """,
                    embedding=embedding,
                    project=project,
                )
                dup_record = dup_result.single()

                if dup_record and dup_record["score"] > 0.95:
                    duration = int((time.time() - start) * 1000)
                    logger.info(
                        f"Skipped duplicate Decision (score={dup_record['score']:.3f}) ({duration}ms)",
                        extra={"cat": "tool"},
                    )
                    return {
                        "action": "skipped",
                        "existing_id": dup_record["id"],
                        "similarity": dup_record["score"],
                    }

            # Create the decision node directly (no session)
            session.run(
                """
                CREATE (d:Decision {id: $decision_id})
                SET d.description = $description,
                    d.timestamp = datetime(),
                    d.project = $project,
                    d.user_id = $user_id,
                    d.status = 'developmental',
                    d.embedding = $embedding,
                    d.topics = $topics
                SET d += $props
                """,
                decision_id=decision_id,
                description=description,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                topics=topics or [],
                props=kwargs,
            )

            # Link to similar prior decisions
            superseded_ids = []
            if embedding:
                link_result = session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    CALL db.index.vector.queryNodes('decision_embedding', 5, $embedding)
                    YIELD node, score
                    WHERE node.project = $project
                      AND node.id <> $decision_id
                      AND score > 0.8
                    WITH d, node, score
                    CALL {
                        WITH d, node, score
                        WITH d, node, score WHERE score > 0.85
                        CREATE (d)-[:SUPERSEDES {similarity: score, auto: true}]->(node)
                        RETURN 'superseded' as rel_type
                        UNION ALL
                        WITH d, node, score
                        WITH d, node, score WHERE score <= 0.85 AND score > 0.8
                        CREATE (d)-[:CITES {similarity: score, auto: true}]->(node)
                        RETURN 'cited' as rel_type
                    }
                    RETURN node.id as linked_id, score, rel_type
                    """,
                    decision_id=decision_id,
                    embedding=embedding,
                    project=project,
                )
                for record in link_result:
                    if record["rel_type"] == "superseded":
                        superseded_ids.append(record["linked_id"])

        duration = int((time.time() - start) * 1000)
        if superseded_ids:
            logger.info(
                f"Created Decision id={decision_id[:12]}... supersedes {len(superseded_ids)} prior ({duration}ms)",
                extra={
                    "cat": "tool",
                    "event": "node_created",
                    "node_type": "Decision",
                    "project": project,
                },
            )
            return {"action": "superseded", "superseded_ids": superseded_ids}
        else:
            logger.info(
                f"Created Decision id={decision_id[:12]}... ({duration}ms)",
                extra={
                    "cat": "tool",
                    "event": "node_created",
                    "node_type": "Decision",
                    "project": project,
                },
            )
            return {"action": "created"}

    def createCorrection(
        self,
        correction_id: str,
        project: str,
        wrong_belief: str,
        right_belief: str,
        embedding: list,
        topics: list[str] | None = None,
        **kwargs,
    ) -> dict:
        logger.debug(f"createCorrection(id={correction_id[:12]}..., project={project})")
        start = time.time()

        dup = self._isDuplicate("correction_embedding", project, embedding, 0.9)
        if dup:
            duration = int((time.time() - start) * 1000)
            logger.info(
                f"Skipped duplicate Correction (score={dup['score']:.3f}) ({duration}ms)",
                extra={"cat": "tool"},
            )
            return {
                "action": "skipped",
                "existing_id": dup["id"],
                "similarity": dup["score"],
            }

        with self.driver.session() as session:
            session.run(
                """
                CREATE (c:Correction {id: $correction_id})
                SET c.wrong_belief = $wrong_belief,
                    c.right_belief = $right_belief,
                    c.timestamp = datetime(),
                    c.project = $project,
                    c.user_id = $user_id,
                    c.embedding = $embedding,
                    c.topics = $topics
                SET c += $props
                """,
                correction_id=correction_id,
                wrong_belief=wrong_belief,
                right_belief=right_belief,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                topics=topics or [],
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created Correction id={correction_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "Correction",
                "project": project,
            },
        )
        return {"action": "created"}

    def createException(
        self,
        exception_id: str,
        project: str,
        rule_broken: str,
        justification: str,
        embedding: list,
        topics: list[str] | None = None,
        **kwargs,
    ) -> dict:
        logger.debug(f"createException(id={exception_id[:12]}..., project={project})")
        start = time.time()

        dup = self._isDuplicate("exception_embedding", project, embedding, 0.9)
        if dup:
            duration = int((time.time() - start) * 1000)
            logger.info(
                f"Skipped duplicate Exception (score={dup['score']:.3f}) ({duration}ms)",
                extra={"cat": "tool"},
            )
            return {
                "action": "skipped",
                "existing_id": dup["id"],
                "similarity": dup["score"],
            }

        with self.driver.session() as session:
            session.run(
                """
                CREATE (e:Exception {id: $exception_id})
                SET e.rule_broken = $rule_broken,
                    e.justification = $justification,
                    e.timestamp = datetime(),
                    e.project = $project,
                    e.user_id = $user_id,
                    e.embedding = $embedding,
                    e.topics = $topics
                SET e += $props
                """,
                exception_id=exception_id,
                rule_broken=rule_broken,
                justification=justification,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                topics=topics or [],
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created Exception id={exception_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "Exception",
                "project": project,
            },
        )
        return {"action": "created"}

    def createInsight(
        self,
        insight_id: str,
        project: str,
        category: str,
        summary: str,
        embedding: list,
        topics: list[str] | None = None,
        **kwargs,
    ) -> dict:
        logger.debug(f"createInsight(id={insight_id[:12]}..., project={project})")
        start = time.time()

        dup = self._isDuplicate("insight_embedding", project, embedding, 0.9)
        if dup:
            duration = int((time.time() - start) * 1000)
            logger.info(
                f"Skipped duplicate Insight (score={dup['score']:.3f}) ({duration}ms)",
                extra={"cat": "tool"},
            )
            return {
                "action": "skipped",
                "existing_id": dup["id"],
                "similarity": dup["score"],
            }

        with self.driver.session() as session:
            session.run(
                """
                CREATE (i:Insight {id: $insight_id})
                SET i.category = $category,
                    i.summary = $summary,
                    i.timestamp = datetime(),
                    i.project = $project,
                    i.user_id = $user_id,
                    i.embedding = $embedding,
                    i.topics = $topics
                SET i += $props
                """,
                insight_id=insight_id,
                category=category,
                summary=summary,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                topics=topics or [],
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created Insight id={insight_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "Insight",
                "project": project,
            },
        )
        return {"action": "created"}

    def createQuestion(
        self,
        question_id: str,
        project: str,
        question: str,
        answer: str,
        embedding: list | None = None,
        topics: list[str] | None = None,
        **kwargs,
    ) -> dict:
        logger.debug(f"createQuestion(id={question_id[:12]}..., project={project})")
        start = time.time()

        if embedding:
            dup = self._isDuplicate("question_embedding", project, embedding, 0.9)
            if dup:
                duration = int((time.time() - start) * 1000)
                logger.info(
                    f"Skipped duplicate Question (score={dup['score']:.3f}) ({duration}ms)",
                    extra={"cat": "tool"},
                )
                return {
                    "action": "skipped",
                    "existing_id": dup["id"],
                    "similarity": dup["score"],
                }

        with self.driver.session() as session:
            session.run(
                """
                CREATE (q:Question {id: $question_id})
                SET q.question = $question,
                    q.answer = $answer,
                    q.timestamp = datetime(),
                    q.project = $project,
                    q.user_id = $user_id,
                    q.embedding = $embedding,
                    q.topics = $topics
                SET q += $props
                """,
                question_id=question_id,
                question=question,
                answer=answer,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                topics=topics or [],
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created Question id={question_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "Question",
                "project": project,
            },
        )
        return {"action": "created"}

    def createFailedApproach(
        self,
        fa_id: str,
        project: str,
        approach: str,
        outcome: str,
        lesson: str,
        embedding: list | None = None,
        topics: list[str] | None = None,
        **kwargs,
    ) -> dict:
        logger.debug(f"createFailedApproach(id={fa_id[:12]}..., project={project})")
        start = time.time()

        if embedding:
            dup = self._isDuplicate("failedapproach_embedding", project, embedding, 0.9)
            if dup:
                duration = int((time.time() - start) * 1000)
                logger.info(
                    f"Skipped duplicate FailedApproach (score={dup['score']:.3f}) ({duration}ms)",
                    extra={"cat": "tool"},
                )
                return {
                    "action": "skipped",
                    "existing_id": dup["id"],
                    "similarity": dup["score"],
                }

        with self.driver.session() as session:
            session.run(
                """
                CREATE (f:FailedApproach {id: $fa_id})
                SET f.approach = $approach,
                    f.outcome = $outcome,
                    f.lesson = $lesson,
                    f.timestamp = datetime(),
                    f.project = $project,
                    f.user_id = $user_id,
                    f.embedding = $embedding,
                    f.topics = $topics
                SET f += $props
                """,
                fa_id=fa_id,
                approach=approach,
                outcome=outcome,
                lesson=lesson,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                topics=topics or [],
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created FailedApproach id={fa_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "FailedApproach",
                "project": project,
            },
        )
        return {"action": "created"}

    def createReference(
        self,
        ref_id: str,
        project: str,
        ref_type: str,
        uri: str,
        **kwargs,
    ):
        logger.debug(f"createReference(id={ref_id[:12]}..., type={ref_type})")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                CREATE (r:Reference {id: $ref_id})
                SET r.type = $ref_type,
                    r.uri = $uri,
                    r.timestamp = datetime(),
                    r.project = $project,
                    r.user_id = $user_id
                SET r += $props
                """,
                ref_id=ref_id,
                ref_type=ref_type,
                uri=uri,
                project=project,
                user_id=self.user_id,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created Reference id={ref_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "Reference",
                "project": project,
            },
        )

    def createDecisionRelationship(
        self,
        decision_id: str,
        project: str,
        target_description: str,
        relationship_type: str,
        reason: str,
        embedding: list,
    ) -> bool:
        """Create explicit relationship from decision to a matching prior decision.

        Finds the best matching prior decision by description similarity
        and creates the specified relationship.

        Returns True if relationship was created, False if no match found.
        """
        logger.debug(
            f"createDecisionRelationship(from={decision_id[:12]}..., type={relationship_type})"
        )
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.vector.queryNodes('decision_embedding', 5, $embedding)
                YIELD node, score
                WHERE node.project = $project
                  AND node.id <> $decision_id
                  AND score > 0.7
                RETURN node.id as target_id, node.description as description, score
                ORDER BY score DESC
                LIMIT 1
                """,
                embedding=embedding,
                project=project,
                decision_id=decision_id,
            )
            record = result.single()

            if not record:
                logger.debug(
                    f"No matching decision found for relationship to: {target_description[:50]}..."
                )
                return False

            rel_type = relationship_type.upper().replace(" ", "_")
            if rel_type not in (
                "SUPERSEDES",
                "DEPENDS_ON",
                "CONSTRAINS",
                "CONFLICTS_WITH",
                "IMPACTS",
            ):
                logger.warning(f"Unknown relationship type: {rel_type}, using IMPACTS")
                rel_type = "IMPACTS"

            session.run(
                f"""
                MATCH (d:Decision {{id: $decision_id}})
                MATCH (target:Decision {{id: $target_id}})
                CREATE (d)-[:{rel_type} {{reason: $reason, auto: false, similarity: $score}}]->(target)
                """,
                decision_id=decision_id,
                target_id=record["target_id"],
                reason=reason,
                score=record["score"],
            )
            logger.info(
                f"Created {rel_type} relationship from {decision_id[:12]} to {record['target_id'][:12]}",
                extra={"cat": "tool"},
            )
            return True

    def createProjectFact(
        self,
        fact_id: str,
        project: str,
        category: str,
        fact: str,
        embedding: list,
        **kwargs,
    ):
        logger.debug(f"createProjectFact(id={fact_id[:12]}..., project={project})")
        start = time.time()
        with self.driver.session() as session:
            session.run(
                """
                CREATE (pf:ProjectFact {id: $fact_id})
                SET pf.category = $category,
                    pf.fact = $fact,
                    pf.timestamp = datetime(),
                    pf.project = $project,
                    pf.user_id = $user_id,
                    pf.embedding = $embedding
                SET pf += $props
                """,
                fact_id=fact_id,
                category=category,
                fact=fact,
                project=project,
                user_id=self.user_id,
                embedding=embedding,
                props=kwargs,
            )
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Created ProjectFact id={fact_id[:12]}... ({duration}ms)",
            extra={
                "cat": "tool",
                "event": "node_created",
                "node_type": "ProjectFact",
                "project": project,
            },
        )

    # === Domain 1: Query Functions ===

    def queryRecent(self, project: str, limit: int = 20, include_team: bool = True):
        """Get recent context for a project (all node types by timestamp)."""
        logger.debug(f"queryRecent(project={project}, limit={limit})")
        start = time.time()
        with self.driver.session() as session:
            if include_team and self.user_id:
                visibility = "(n.status = 'curated' OR n.user_id = $user_id)"
            else:
                visibility = "n.user_id = $user_id" if self.user_id else "true"

            # Query all Domain 1 node types directly by project + timestamp
            result = session.run(
                f"""
                CALL {{
                    MATCH (n:Decision {{project: $project}}) WHERE {visibility}
                    RETURN n, 'Decision' as node_type
                    UNION ALL
                    MATCH (n:Correction {{project: $project}}) WHERE {visibility}
                    RETURN n, 'Correction' as node_type
                    UNION ALL
                    MATCH (n:Insight {{project: $project}}) WHERE {visibility}
                    RETURN n, 'Insight' as node_type
                    UNION ALL
                    MATCH (n:Exception {{project: $project}}) WHERE {visibility}
                    RETURN n, 'Exception' as node_type
                    UNION ALL
                    MATCH (n:FailedApproach {{project: $project}}) WHERE {visibility}
                    RETURN n, 'FailedApproach' as node_type
                }}
                RETURN n, node_type
                ORDER BY n.timestamp DESC
                LIMIT $limit
                """,
                project=project,
                user_id=self.user_id,
                limit=limit,
            )
            records = [
                {"n": dict(record["n"]), "node_type": record["node_type"]}
                for record in result
            ]
        duration = int((time.time() - start) * 1000)
        logger.debug(f"queryRecent returned {len(records)} items ({duration}ms)")
        return records

    def searchPrecedent(
        self, query: str, project: str, limit: int = 10, include_team: bool = True
    ):
        """Full-text search across all node types."""
        with self.driver.session() as session:
            results = {}
            indexes = [
                ("decision_search", "decisions"),
                ("correction_search", "corrections"),
                ("insight_search", "insights"),
                ("question_search", "questions"),
                ("failedapproach_search", "failed_approaches"),
                ("projectfact_search", "project_facts"),
                ("exception_search", "exceptions"),
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
        """Vector similarity search across Domain 1."""
        with self.driver.session() as session:
            results = {}
            indexes = [
                ("decision_embedding", "decisions"),
                ("correction_embedding", "corrections"),
                ("insight_embedding", "insights"),
                ("projectfact_embedding", "project_facts"),
                ("exception_embedding", "exceptions"),
                ("failedapproach_embedding", "failed_approaches"),
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

    def queryByTopic(self, project: str, topic: str, limit: int = 20):
        """Get decisions/items by topic."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                WHERE $topic IN d.topics
                RETURN d
                ORDER BY d.timestamp DESC
                LIMIT $limit
                """,
                project=project,
                topic=topic,
                limit=limit,
            )
            return [dict(record["d"]) for record in result]

    def queryStaleDecisions(self, project: str, days: int = 30):
        """Find developmental decisions that may need review."""
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

    def queryProjectFacts(self, project: str, limit: int = 20):
        """Get project facts (conventions, tools, patterns)."""
        logger.debug(f"queryProjectFacts(project={project}, limit={limit})")
        start = time.time()
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (pf:ProjectFact {project: $project})
                RETURN pf
                ORDER BY pf.timestamp DESC
                LIMIT $limit
                """,
                project=project,
                limit=limit,
            )
            records = [dict(record["pf"]) for record in result]
        duration = int((time.time() - start) * 1000)
        logger.debug(f"queryProjectFacts returned {len(records)} items ({duration}ms)")
        return records

    def queryOpenQuestions(self, project: str, limit: int = 10):
        """Get unanswered questions."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (q:Question {project: $project})
                WHERE q.answer IS NULL OR q.answer = ''
                RETURN q
                ORDER BY q.timestamp DESC
                LIMIT $limit
                """,
                project=project,
                limit=limit,
            )
            return [dict(record["q"]) for record in result]

    # === Pattern Detection (for dashboard) ===

    def queryExceptionClusters(self, project: str) -> list[dict]:
        """Find rules with multiple exceptions."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Exception {project: $project})
                WITH e.rule_broken as rule, count(e) as count, collect(e.justification) as justifications
                WHERE count >= 2
                RETURN rule, count, justifications
                ORDER BY count DESC
                """,
                project=project,
            )
            return [dict(record) for record in result]

    def querySupersessionChains(self, project: str) -> list[dict]:
        """Find decisions that evolved through multiple iterations."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (newest:Decision {project: $project})-[:SUPERSEDES*2..]->(oldest:Decision)
                WHERE NOT EXISTS { (x:Decision)-[:SUPERSEDES]->(newest) }
                WITH newest, oldest, length(path) as chain_length,
                     [n IN nodes(path) | n.description] as descriptions
                RETURN newest.id as newest_id, newest.description as newest_desc,
                       oldest.description as oldest_desc, chain_length, descriptions
                ORDER BY chain_length DESC
                LIMIT 10
                """,
                project=project,
            )
            return [dict(record) for record in result]

    def queryCorrectionHotspots(self, project: str) -> list[dict]:
        """Find topics with high correction counts."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Correction {project: $project})
                WHERE c.topics IS NOT NULL AND size(c.topics) > 0
                UNWIND c.topics as topic
                WITH topic, count(c) as count, collect(c.right_belief)[0..3] as samples
                WHERE count >= 2
                RETURN topic, count, samples
                ORDER BY count DESC
                """,
                project=project,
            )
            return [dict(record) for record in result]

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

    def recordRetrieval(
        self,
        project: str,
        retrieved_ids: list[str],
        context_summary: str,
    ):
        """Record what context was retrieved."""
        with self.driver.session() as session:
            session.run(
                """
                CREATE (r:Retrieval {
                    id: $id,
                    project: $project,
                    user_id: $user_id,
                    timestamp: datetime(),
                    retrieved_ids: $retrieved_ids,
                    retrieved_count: $count,
                    context_summary: $context_summary
                })
                """,
                id=f"retrieval-{uuid.uuid4().hex[:12]}",
                project=project,
                user_id=self.user_id,
                retrieved_ids=retrieved_ids,
                count=len(retrieved_ids),
                context_summary=context_summary[:2000],
            )

    def queryRetrievals(self, project: str, limit: int = 50) -> list[dict]:
        """Get recent retrieval events."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (r:Retrieval {project: $project})
                RETURN r ORDER BY r.timestamp DESC LIMIT $limit
                """,
                project=project,
                limit=limit,
            )
            return [dict(record["r"]) for record in result]

    # === Metrics ===

    def calculateCoefficient(self, project: str) -> float:
        """Calculate cognitive coefficient from observable metrics."""
        curated = self._countNodes("Decision", project, status="curated")
        reuse_rate = self.calculateDecisionReuseRate(project)

        coefficient = 1.0 + (curated * 0.02) + (reuse_rate * 1.0)
        return min(4.0, coefficient)

    def calculateDecisionReuseRate(self, project: str) -> float:
        """Calculate decision reuse rate (decisions with precedent links)."""
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
            "decision_reuse_rate": self.calculateDecisionReuseRate(project),
            "graph_density": self.calculateGraphDensity(project),
            "total_decisions": self._countNodes("Decision", project),
            "total_corrections": self._countNodes("Correction", project),
            "total_insights": self._countNodes("Insight", project),
            "total_exceptions": self._countNodes("Exception", project),
            "total_failed_approaches": self._countNodes("FailedApproach", project),
            "total_project_facts": self._countNodes("ProjectFact", project),
            "total_questions": self._countNodes("Question", project),
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
