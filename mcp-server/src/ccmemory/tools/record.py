"""MCP tools for recording context to the graph.

Per doc/clarifications/1-DAG-with-CROSS-REFS.md:
- No session dependency
- All nodes created directly with project + timestamp
"""

import uuid
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..graph import getClient
from ..embeddings import getEmbedding
from ..context import getCurrentProject
from .logging import logTool


def _projectError() -> dict:
    return {
        "error": "project_not_found",
        "message": "No project context available. Start a new session or specify project.",
        "ask_user": True,
        "ask_user_options": [
            {"label": "Retry (re-establish session)", "action": "retry"},
            {"label": "Continue without saving", "action": "skip"},
        ],
        "instructions": (
            "Use AskUserQuestion to ask the user: "
            "'The ccmemory project context was lost. Would you like to retry "
            "(which will re-establish the context) or continue without saving?'"
        ),
    }


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
        topics: Optional[list[str]] = None,
    ) -> dict:
        """Record a decision to the context graph.

        Args:
            description: What was decided
            rationale: Why this choice was made
            options_considered: What alternatives were evaluated
            revisit_trigger: Conditions that should prompt reconsideration
            sets_precedent: Whether this decision should guide future similar decisions
            topics: Topics/components this decision relates to (e.g., ['auth', 'api'])
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        decision_id = f"decision-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"{description} {rationale or ''}"
        embedding = getEmbedding(text_for_embedding)

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0,
        }
        if rationale:
            kwargs["rationale"] = rationale
        if options_considered:
            kwargs["options_considered"] = options_considered
        if revisit_trigger:
            kwargs["revisit_trigger"] = revisit_trigger
        if sets_precedent:
            kwargs["sets_precedent"] = sets_precedent

        result = client.createDecision(
            decision_id=decision_id,
            project=project,
            description=description,
            embedding=embedding,
            topics=topics or [],
            **kwargs,
        )

        return {"decision_id": decision_id, "status": "recorded", **result}

    @mcp.tool()
    @logTool
    async def recordCorrection(
        wrong_belief: str,
        right_belief: str,
        severity: str = "significant",
        topics: Optional[list[str]] = None,
    ) -> dict:
        """Record a correction to Claude's understanding.

        Args:
            wrong_belief: What Claude incorrectly believed
            right_belief: The correct understanding
            severity: How significant the error was (minor/significant/critical)
            topics: Topics/components this correction relates to
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        correction_id = f"correction-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"Wrong: {wrong_belief} Correct: {right_belief}"
        embedding = getEmbedding(text_for_embedding)

        client.createCorrection(
            correction_id=correction_id,
            project=project,
            wrong_belief=wrong_belief,
            right_belief=right_belief,
            embedding=embedding,
            topics=topics or [],
            severity=severity,
            detection_method="explicit_command",
            detection_confidence=1.0,
        )

        return {"correction_id": correction_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordException(
        rule_broken: str,
        justification: str,
        scope: str = "one-time",
        topics: Optional[list[str]] = None,
    ) -> dict:
        """Record an exception to normal rules.

        Args:
            rule_broken: The rule or standard practice being bypassed
            justification: Why this exception is appropriate
            scope: How broadly this exception applies (one-time/conditional/new-precedent)
            topics: Topics/components this exception relates to
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        exception_id = f"exception-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"Exception to: {rule_broken} Because: {justification}"
        embedding = getEmbedding(text_for_embedding)

        client.createException(
            exception_id=exception_id,
            project=project,
            rule_broken=rule_broken,
            justification=justification,
            embedding=embedding,
            topics=topics or [],
            scope=scope,
            detection_method="explicit_command",
            detection_confidence=1.0,
        )

        return {"exception_id": exception_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordInsight(
        summary: str,
        category: str = "realization",
        detail: Optional[str] = None,
        implications: Optional[str] = None,
        topics: Optional[list[str]] = None,
    ) -> dict:
        """Record an insight or realization.

        Args:
            summary: Brief description of the insight
            category: Type of insight (realization/analysis/strategy/personal/synthesis)
            detail: Full elaboration of the insight
            implications: What this insight means for future work
            topics: Topics/components this insight relates to
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        insight_id = f"insight-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"{summary} {detail or ''} {implications or ''}"
        embedding = getEmbedding(text_for_embedding)

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0,
        }
        if detail:
            kwargs["detail"] = detail
        if implications:
            kwargs["implications"] = implications

        client.createInsight(
            insight_id=insight_id,
            project=project,
            category=category,
            summary=summary,
            embedding=embedding,
            topics=topics or [],
            **kwargs,
        )

        return {"insight_id": insight_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordQuestion(
        question: str,
        answer: Optional[str] = None,
        context: Optional[str] = None,
        topics: Optional[list[str]] = None,
    ) -> dict:
        """Record a question (optionally with answer).

        Args:
            question: The question that was asked
            answer: The answer (if known). Leave empty for open questions.
            context: Why this question matters
            topics: Topics/components this question relates to
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        question_id = f"question-{uuid.uuid4().hex[:8]}"

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0,
        }
        if context:
            kwargs["context"] = context

        client.createQuestion(
            question_id=question_id,
            project=project,
            question=question,
            answer=answer or "",
            topics=topics or [],
            **kwargs,
        )

        return {"question_id": question_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordFailedApproach(
        approach: str,
        outcome: str,
        lesson: str,
        topics: Optional[list[str]] = None,
    ) -> dict:
        """Record an approach that was tried and didn't work.

        Args:
            approach: What was attempted
            outcome: What happened (why it failed)
            lesson: What was learned
            topics: Topics/components this relates to
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        fa_id = f"failed-{uuid.uuid4().hex[:8]}"

        text_for_embedding = f"{approach} {outcome} {lesson}"
        embedding = getEmbedding(text_for_embedding)

        client.createFailedApproach(
            fa_id=fa_id,
            project=project,
            approach=approach,
            outcome=outcome,
            lesson=lesson,
            embedding=embedding,
            topics=topics or [],
            detection_method="explicit_command",
            detection_confidence=1.0,
        )

        return {"failed_approach_id": fa_id, "status": "recorded"}

    @mcp.tool()
    @logTool
    async def recordReference(
        uri: str,
        ref_type: str = "url",
        description: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """Record a reference to an external resource.

        Args:
            uri: The URL or file path
            ref_type: Type of reference (url/file_path/documentation)
            description: What this reference is about
            context: Why this reference matters
        """
        project = getCurrentProject()
        if not project:
            return _projectError()

        client = getClient()
        ref_id = f"ref-{uuid.uuid4().hex[:8]}"

        kwargs = {
            "detection_method": "explicit_command",
            "detection_confidence": 1.0,
        }
        if description:
            kwargs["description"] = description
        if context:
            kwargs["context"] = context

        client.createReference(
            ref_id=ref_id,
            project=project,
            ref_type=ref_type,
            uri=uri,
            **kwargs,
        )

        return {"reference_id": ref_id, "status": "recorded"}
