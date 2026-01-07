"""MCP tools for recording context to the graph."""

import uuid
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..graph import getClient
from ..embeddings import getEmbedding
from ..context import getCurrentProject, getCurrentSessionId
from .logging import logTool


def registerRecordTools(mcp: FastMCP):
    """Register all record tools with the MCP server."""

    @mcp.tool()
    @logTool
    async def recordDecision(
        description: str,
        rationale: Optional[str] = None,
        options_considered: Optional[str] = None,
        revisit_trigger: Optional[str] = None,
        sets_precedent: bool = False,
        session_id: Optional[str] = None
    ) -> dict:
        """Record a decision to the context graph.

        Args:
            description: What was decided
            rationale: Why this choice was made
            options_considered: What alternatives were evaluated
            revisit_trigger: Conditions that should prompt reconsideration
            sets_precedent: Whether this decision should guide future similar decisions
            session_id: Session to link this decision to
        """
        client = getClient()
        decision_id = f"decision-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"{description} {rationale or ''}"
        embedding = getEmbedding(text_for_embedding)

        kwargs = {}
        if rationale:
            kwargs["rationale"] = rationale
        if options_considered:
            kwargs["options_considered"] = options_considered
        if revisit_trigger:
            kwargs["revisit_trigger"] = revisit_trigger
        if sets_precedent:
            kwargs["sets_precedent"] = sets_precedent
        kwargs["detection_method"] = "explicit_command"
        kwargs["detection_confidence"] = 1.0

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createDecision(
                decision_id=decision_id,
                session_id=effective_session,
                description=description,
                embedding=embedding,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
                    """
                    CREATE (d:Decision {id: $decision_id})
                    SET d.description = $description,
                        d.timestamp = datetime(),
                        d.project = $project,
                        d.user_id = $user_id,
                        d.status = 'developmental',
                        d.embedding = $embedding
                    SET d += $props
                    """,
                    decision_id=decision_id,
                    description=description,
                    project=project,
                    user_id=client.user_id,
                    embedding=embedding,
                    props=kwargs
                )

        return {"decision_id": decision_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordCorrection(
        wrong_belief: str,
        right_belief: str,
        severity: str = "significant",
        session_id: Optional[str] = None
    ) -> dict:
        """Record a correction to Claude's understanding.

        Args:
            wrong_belief: What Claude incorrectly believed
            right_belief: The correct understanding
            severity: How significant the error was (minor/significant/critical)
            session_id: Session to link this correction to
        """
        client = getClient()
        correction_id = f"correction-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"Wrong: {wrong_belief} Correct: {right_belief}"
        embedding = getEmbedding(text_for_embedding)

        kwargs = {
            "severity": severity,
            "detection_method": "explicit_command",
            "detection_confidence": 1.0
        }

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createCorrection(
                correction_id=correction_id,
                session_id=effective_session,
                wrong_belief=wrong_belief,
                right_belief=right_belief,
                embedding=embedding,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
                    """
                    CREATE (c:Correction {id: $correction_id})
                    SET c.wrong_belief = $wrong_belief,
                        c.right_belief = $right_belief,
                        c.timestamp = datetime(),
                        c.project = $project,
                        c.user_id = $user_id,
                        c.embedding = $embedding
                    SET c += $props
                    """,
                    correction_id=correction_id,
                    wrong_belief=wrong_belief,
                    right_belief=right_belief,
                    project=project,
                    user_id=client.user_id,
                    embedding=embedding,
                    props=kwargs
                )

        return {"correction_id": correction_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordException(
        rule_broken: str,
        justification: str,
        scope: str = "one-time",
        session_id: Optional[str] = None
    ) -> dict:
        """Record an exception to normal rules.

        Args:
            rule_broken: The rule or standard practice being bypassed
            justification: Why this exception is appropriate
            scope: How broadly this exception applies (one-time/conditional/new-precedent)
            session_id: Session to link this exception to
        """
        client = getClient()
        exception_id = f"exception-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"Exception to: {rule_broken} Because: {justification}"
        embedding = getEmbedding(text_for_embedding)

        kwargs = {
            "scope": scope,
            "detection_method": "explicit_command",
            "detection_confidence": 1.0
        }

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createException(
                exception_id=exception_id,
                session_id=effective_session,
                rule_broken=rule_broken,
                justification=justification,
                embedding=embedding,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
                    """
                    CREATE (e:Exception {id: $exception_id})
                    SET e.rule_broken = $rule_broken,
                        e.justification = $justification,
                        e.timestamp = datetime(),
                        e.project = $project,
                        e.user_id = $user_id,
                        e.embedding = $embedding
                    SET e += $props
                    """,
                    exception_id=exception_id,
                    rule_broken=rule_broken,
                    justification=justification,
                    project=project,
                    user_id=client.user_id,
                    embedding=embedding,
                    props=kwargs
                )

        return {"exception_id": exception_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordInsight(
        summary: str,
        category: str = "realization",
        detail: Optional[str] = None,
        implications: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """Record an insight or realization.

        Args:
            summary: Brief description of the insight
            category: Type of insight (realization/analysis/strategy/personal/synthesis)
            detail: Full elaboration of the insight
            implications: What this insight means for future work
            session_id: Session to link this insight to
        """
        client = getClient()
        insight_id = f"insight-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"{summary} {detail or ''} {implications or ''}"
        embedding = getEmbedding(text_for_embedding)

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0
        }
        if detail:
            kwargs["detail"] = detail
        if implications:
            kwargs["implications"] = implications

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createInsight(
                insight_id=insight_id,
                session_id=effective_session,
                category=category,
                summary=summary,
                embedding=embedding,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
                    """
                    CREATE (i:Insight {id: $insight_id})
                    SET i.category = $category,
                        i.summary = $summary,
                        i.timestamp = datetime(),
                        i.project = $project,
                        i.user_id = $user_id,
                        i.embedding = $embedding
                    SET i += $props
                    """,
                    insight_id=insight_id,
                    category=category,
                    summary=summary,
                    project=project,
                    user_id=client.user_id,
                    embedding=embedding,
                    props=kwargs
                )

        return {"insight_id": insight_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordQuestion(
        question: str,
        answer: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """Record a meaningful Q&A exchange.

        Args:
            question: The question that was asked
            answer: The answer that was given
            context: Why this Q&A matters
            session_id: Session to link this question to
        """
        client = getClient()
        question_id = f"question-{uuid.uuid4().hex[:8]}"

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0
        }
        if context:
            kwargs["context"] = context

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createQuestion(
                question_id=question_id,
                session_id=effective_session,
                question=question,
                answer=answer,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
                    """
                    CREATE (q:Question {id: $question_id})
                    SET q.question = $question,
                        q.answer = $answer,
                        q.timestamp = datetime(),
                        q.project = $project,
                        q.user_id = $user_id
                    SET q += $props
                    """,
                    question_id=question_id,
                    question=question,
                    answer=answer,
                    project=project,
                    user_id=client.user_id,
                    props=kwargs
                )

        return {"question_id": question_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordFailedApproach(
        approach: str,
        outcome: str,
        lesson: str,
        session_id: Optional[str] = None
    ) -> dict:
        """Record an approach that was tried and didn't work.

        Args:
            approach: What was attempted
            outcome: What happened (why it failed)
            lesson: What was learned
            session_id: Session to link this to
        """
        client = getClient()
        fa_id = f"failed-{uuid.uuid4().hex[:8]}"

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0
        }

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createFailedApproach(
                fa_id=fa_id,
                session_id=effective_session,
                approach=approach,
                outcome=outcome,
                lesson=lesson,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
                    """
                    CREATE (f:FailedApproach {id: $fa_id})
                    SET f.approach = $approach,
                        f.outcome = $outcome,
                        f.lesson = $lesson,
                        f.timestamp = datetime(),
                        f.project = $project,
                        f.user_id = $user_id
                    SET f += $props
                    """,
                    fa_id=fa_id,
                    approach=approach,
                    outcome=outcome,
                    lesson=lesson,
                    project=project,
                    user_id=client.user_id,
                    props=kwargs
                )

        return {"failed_approach_id": fa_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordReference(
        uri: str,
        ref_type: str = "url",
        description: Optional[str] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """Record a reference to an external resource.

        Args:
            uri: The URL or file path
            ref_type: Type of reference (url/file_path/documentation)
            description: What this reference is about
            context: Why this reference matters
            session_id: Session to link this to
        """
        client = getClient()
        ref_id = f"ref-{uuid.uuid4().hex[:8]}"

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0
        }
        if description:
            kwargs["description"] = description
        if context:
            kwargs["context"] = context

        effective_session = session_id or getCurrentSessionId()
        if effective_session:
            client.createReference(
                ref_id=ref_id,
                session_id=effective_session,
                ref_type=ref_type,
                uri=uri,
                **kwargs
            )
        else:
            project = getCurrentProject()
            if not project:
                return {"error": "No active session. Start a Claude Code session first."}
            driver = client.driver
            with driver.session() as db_session:
                db_session.run(
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
                    user_id=client.user_id,
                    props=kwargs
                )

        return {"reference_id": ref_id, "status": "recorded"}
