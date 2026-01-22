"""Hook handlers for Claude Code integration.

Per doc/clarifications/1-DAG-with-CROSS-REFS.md:
- No Session nodes created
- Project facts injected as "Project Rules" (binding instructions)
- All nodes created directly with project + timestamp
"""

import json
import logging
import uuid
from datetime import datetime

from .graph import getClient
from .context import setCurrentProject, clearCurrentProject, getCurrentProject
from .detection.detector import detectAll
from .detection.schemas import (
    Correction,
    Decision,
    Detection,
    DetectionType,
    Exception_,
    FailedApproach,
    Insight,
    ProjectFact,
    Question,
    ReferenceData,
)
from .embeddings import getEmbedding

logger = logging.getLogger("ccmemory")


def handleSessionStart(
    session_id: str, cwd: str, conversation_stems: list[str] | None = None
) -> dict:
    """Initialize context for a new CC session.

    Note: We don't create Session nodes anymore (per clarification).
    Just set in-memory context and return relevant context for injection.
    """
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    client = getClient()

    # Set in-memory context for tools (they need to know current project)
    setCurrentProject(project)

    # Query context to inject
    facts = client.queryProjectFacts(project, limit=15)
    recent = client.queryRecent(project, limit=15)
    stale = client.queryStaleDecisions(project, days=30)
    failed = client.queryFailedApproaches(project, limit=5)

    retrieved_ids = []
    context_parts = []

    # Project Facts as binding instructions (not just context)
    if facts:
        context_parts.append(
            "## Project Rules (from context graph — treat as custom instructions)"
        )
        context_parts.append("")

        # Group by category
        by_category = {}
        for f in facts:
            if f.get("id"):
                retrieved_ids.append(f["id"])
            cat = f.get("category", "general")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f.get("fact", ""))

        for cat, items in by_category.items():
            context_parts.append(f"### {cat.title()}")
            for item in items[:5]:
                context_parts.append(f"- {item[:120]}")
            context_parts.append("")

    # Recent decisions/corrections/insights
    if recent:
        context_parts.append("## Recent Decisions")
        for item in recent[:10]:
            node = item.get("n", {})
            node_type = item.get("node_type", "")
            if not node:
                continue
            if node.get("id"):
                retrieved_ids.append(node["id"])

            topics = node.get("topics", [])
            topic_str = f"[{', '.join(topics[:2])}] " if topics else ""

            if node_type == "Decision":
                context_parts.append(
                    f"- {topic_str}{str(node.get('description', ''))[:100]}"
                )
            elif node_type == "Correction":
                context_parts.append(
                    f"- CORRECTION: {topic_str}{str(node.get('right_belief', ''))[:100]}"
                )
            elif node_type == "Insight":
                context_parts.append(
                    f"- Insight: {topic_str}{str(node.get('summary', ''))[:100]}"
                )
            elif node_type == "Exception":
                context_parts.append(
                    f"- Exception to '{node.get('rule_broken', '')[:40]}': {str(node.get('justification', ''))[:60]}"
                )
        context_parts.append("")

    # Failed approaches prominently
    if failed:
        context_parts.append("## Things That Didn't Work (Don't Repeat)")
        for f in failed[:5]:
            if f.get("id"):
                retrieved_ids.append(f["id"])
            approach = str(f.get("approach", ""))[:50]
            lesson = str(f.get("lesson", ""))[:60]
            context_parts.append(f"- **{approach}**: {lesson}")
        context_parts.append("")

    # Stale decisions
    if stale:
        context_parts.append("## Decisions Needing Review")
        for d in stale[:3]:
            if d.get("id"):
                retrieved_ids.append(d["id"])
            desc = str(d.get("description", ""))[:80]
            context_parts.append(f"- {desc} *(developmental, may need revisit)*")
        context_parts.append("")

    # Empty state
    if not facts and not recent and not stale and not failed:
        context_parts.append("# Context Graph")
        context_parts.append(f"Project: {project}")
        context_parts.append("")
        context_parts.append(
            "No prior context. Project facts, decisions, and corrections will be captured automatically."
        )

    # Pending backfill (kept but simplified)
    pending = _filterPendingBackfill(conversation_stems or [], client)
    if pending:
        context_parts.append("")
        context_parts.append("## Pending History Import")
        context_parts.append(f"Found {len(pending)} conversation(s) not yet imported.")
        context_parts.append("Use AskUserQuestion to offer importing.")

    context_text = "\n".join(context_parts)

    # Record retrieval (telemetry only, not core)
    if retrieved_ids:
        client.recordRetrieval(
            project=project,
            retrieved_ids=retrieved_ids,
            context_summary=context_text,
        )
        logger.info(f"Retrieved {len(retrieved_ids)} items for project {project}")

    return {
        "context": context_text,
        "project": project,
        "pending_backfill": len(pending) if pending else 0,
        "retrieved_count": len(retrieved_ids),
    }


def _filterPendingBackfill(session_stems: list[str], client) -> list[str]:
    """Check which conversation files haven't been backfilled yet."""
    if not session_stems:
        return []
    # For now, just return the list - we'll check by decision content later
    # This is a placeholder until we have a better way to track imports
    return session_stems[:20]  # Cap at 20


def readTranscript(transcript_path: str) -> tuple[str, str, str]:
    """Read the last user message and assistant response from transcript."""
    try:
        with open(transcript_path, "r") as f:
            messages = [json.loads(line) for line in f if line.strip()]
    except (FileNotFoundError, json.JSONDecodeError):
        return "", "", ""

    user_message = ""
    assistant_response = ""
    for msg in reversed(messages):
        inner = msg.get("message", {})
        role = inner.get("role") or msg.get("type")
        if role == "user" and not user_message:
            content = inner.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
            user_message = str(content)
        elif role == "assistant" and not assistant_response:
            content = inner.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
            assistant_response = str(content)
        if user_message and assistant_response:
            break

    context = "\n".join(
        f"{m.get('type', 'unknown')}: {str(m.get('message', {}).get('content', ''))[:200]}"
        for m in messages[-10:-2]
    )
    return user_message, assistant_response, context


def _storeDetection(client, detection: Detection, project: str) -> bool:
    """Store a detection in the graph. Returns True if stored, False if skipped."""
    det_id = f"{detection.type.value}-{uuid.uuid4().hex[:8]}"

    embedding = getEmbedding(detection.data.model_dump_json())

    # Check for duplicate project facts
    if detection.type == DetectionType.ProjectFact and project:
        if client.projectFactExists(project, embedding, threshold=0.9):
            return False

    data = detection.data
    match detection.type:
        case DetectionType.Decision:
            assert isinstance(data, Decision)
            client.createDecision(
                decision_id=det_id,
                project=project,
                description=data.description,
                embedding=embedding,
                topics=getattr(data, "topics", None) or [],
                continues_decision=getattr(data, "continuesDecision", None),
                rationale=data.rationale,
                revisit_trigger=data.revisitTrigger,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
            for rel in getattr(data, "relatedDecisions", None) or []:
                rel_embedding = getEmbedding(rel.description)
                client.createDecisionRelationship(
                    decision_id=det_id,
                    project=project,
                    target_description=rel.description,
                    relationship_type=rel.relationshipType.value,
                    reason=rel.reason,
                    embedding=rel_embedding,
                )
        case DetectionType.Correction:
            assert isinstance(data, Correction)
            client.createCorrection(
                correction_id=det_id,
                project=project,
                wrong_belief=data.wrongBelief,
                right_belief=data.rightBelief,
                embedding=embedding,
                topics=getattr(data, "topics", None) or [],
                severity=data.severity.value,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Exception:
            assert isinstance(data, Exception_)
            client.createException(
                exception_id=det_id,
                project=project,
                rule_broken=data.ruleBroken,
                justification=data.justification,
                embedding=embedding,
                topics=getattr(data, "topics", None) or [],
                scope=data.scope.value,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Insight:
            assert isinstance(data, Insight)
            client.createInsight(
                insight_id=det_id,
                project=project,
                category=data.category.value,
                summary=data.summary,
                embedding=embedding,
                topics=getattr(data, "topics", None) or [],
                implications=data.implications,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Question:
            assert isinstance(data, Question)
            client.createQuestion(
                question_id=det_id,
                project=project,
                question=data.question,
                answer=data.answer,
                embedding=embedding,
                topics=getattr(data, "topics", None) or [],
                context=data.context,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.FailedApproach:
            assert isinstance(data, FailedApproach)
            client.createFailedApproach(
                fa_id=det_id,
                project=project,
                approach=data.approach,
                outcome=data.outcome,
                lesson=data.lesson or "",
                embedding=embedding,
                topics=getattr(data, "topics", None) or [],
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Reference:
            assert isinstance(data, ReferenceData)
            for ref in data.references:
                ref_id = f"ref-{uuid.uuid4().hex[:8]}"
                client.createReference(
                    ref_id=ref_id,
                    project=project,
                    ref_type=ref.type.value,
                    uri=ref.uri,
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
        case DetectionType.ProjectFact:
            assert isinstance(data, ProjectFact)
            client.createProjectFact(
                fact_id=det_id,
                project=project,
                category=data.category.value,
                fact=data.fact,
                embedding=embedding,
                context=data.context,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
    return True


async def handleMessageResponse(
    session_id: str, transcript_path: str, cwd: str
) -> dict:
    """Handle stop hook - detect and store decisions/corrections/etc."""
    user_message, claude_response, context = readTranscript(transcript_path)
    logger.debug(
        f"transcript_path={transcript_path}, user_message_len={len(user_message)}"
    )
    if not user_message:
        logger.debug("No user_message found, skipping detection")
        return {"detections": 0}

    try:
        detections = await detectAll(user_message, claude_response, context)
    except RuntimeError as e:
        logger.exception(f"Detection failed: {e}")
        return {"detections": 0, "error": str(e)}

    if not detections:
        prompt_preview = (
            user_message[:80] + "..." if len(user_message) > 80 else user_message
        )
        logger.info(
            prompt_preview,
            extra={"cat": "prompt", "event": "no_mutation"},
        )
        return {"detections": 0}

    client = getClient()
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    stored = 0

    for detection in detections:
        try:
            if _storeDetection(client, detection, project):
                stored += 1
        except (ValueError, RuntimeError, AssertionError):
            continue

    client.recordTelemetry(
        event_type="detections",
        project=project,
        data={"count": stored, "types": [d.type.value for d in detections]},
    )

    return {"detections": stored}


def handleSessionEnd(session_id: str, transcript_path: str | None, cwd: str) -> dict:
    """Handle session end - just clear in-memory context."""
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    client = getClient()

    clearCurrentProject()

    client.recordTelemetry(
        event_type="session_end", project=project, data={"session_id": session_id}
    )

    return {"session_ended": session_id, "project": project}
