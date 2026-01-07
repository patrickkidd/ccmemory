import json
import uuid
import asyncio
from datetime import datetime

from .graph import getClient
from .context import setCurrentSession, clearCurrentSession
from .detection.detector import detectAll
from .detection.schemas import (
    Correction,
    Decision,
    Detection,
    DetectionType,
    Exception_,
    FailedApproach,
    Insight,
    Question,
    ReferenceData,
)
from .embeddings import getEmbedding


def filterPendingBackfillSessions(session_stems: list[str], client=None) -> list[str]:
    """Given session stems from host filesystem, return those not yet backfilled."""
    if not session_stems:
        return []

    if client is None:
        client = getClient()

    # Batch check for efficiency
    backfill_ids = [f"backfill-{s}" for s in session_stems]
    existing = client.filterExistingSessions(backfill_ids)
    return [s for s in session_stems if f"backfill-{s}" not in existing]


def handleSessionStart(
    session_id: str, cwd: str, conversation_stems: list[str] | None = None
) -> dict:
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    client = getClient()

    setCurrentSession(project, session_id)

    client.createSession(
        session_id=session_id, project=project, started_at=datetime.now().isoformat()
    )

    recent = client.queryRecent(project, limit=15)
    stale = client.queryStaleDecisions(project, days=30)
    failed = client.queryFailedApproaches(project, limit=5)

    context_parts = [
        f"# Context Graph: {project}",
        f"Session: {session_id[:12]}...",
        "",
    ]

    if recent:
        context_parts.append("## Recent Context")
        for item in recent[:10]:
            node = item.get("n", {})
            if not node:
                continue
            if "description" in node:
                context_parts.append(f"- Decision: {str(node['description'])[:100]}")
            elif "wrong_belief" in node:
                context_parts.append(f"- Correction: {str(node['right_belief'])[:100]}")
            elif "summary" in node:
                context_parts.append(f"- Insight: {str(node['summary'])[:100]}")

    if stale:
        context_parts.append("")
        context_parts.append("## Decisions Needing Review")
        for d in stale[:3]:
            desc = str(d.get("description", ""))[:80]
            context_parts.append(
                f"- {desc} (developmental, may need revisit)"
            )

    if failed:
        context_parts.append("")
        context_parts.append("## Failed Approaches (Don't Repeat)")
        for f in failed[:3]:
            context_parts.append(
                f"- {str(f.get('approach', ''))[:60]}: {str(f.get('lesson', ''))[:60]}"
            )

    if not recent and not stale and not failed:
        context_parts.append(
            "No prior context. Decisions, corrections, and insights will be captured."
        )

    pending = filterPendingBackfillSessions(conversation_stems or [], client)
    if pending:
        context_parts.append("")
        context_parts.append("## Pending History Import")
        context_parts.append(f"Found {len(pending)} conversation(s) not yet imported.")
        context_parts.append("Use AskUserQuestion to offer importing:")
        context_parts.append('- "Import 10 conversations" (Recommended)')
        context_parts.append('- "Import all conversations"')
        context_parts.append('- "Skip import"')
        context_parts.append("If user accepts, call ccmemory_list_conversations then")
        context_parts.append("ccmemory_backfill_conversation for each session.")

    return {
        "context": "\n".join(context_parts),
        "project": project,
        "pending_backfill": len(pending) if pending else 0,
    }


def readTranscript(transcript_path: str) -> tuple[str, str, str]:
    try:
        with open(transcript_path, "r") as f:
            messages = [json.loads(line) for line in f if line.strip()]
    except (FileNotFoundError, json.JSONDecodeError):
        return "", "", ""

    user_message = ""
    assistant_response = ""
    for msg in reversed(messages):
        if msg.get("role") == "user" and not user_message:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
            user_message = str(content)
        elif msg.get("role") == "assistant" and not assistant_response:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
            assistant_response = str(content)
        if user_message and assistant_response:
            break

    context = "\n".join(
        f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:200]}"
        for m in messages[-10:-2]
    )
    return user_message, assistant_response, context


def _storeDetection(client, session_id: str, detection: Detection) -> bool:
    det_id = f"{detection.type.value}-{uuid.uuid4().hex[:8]}"

    try:
        embedding = getEmbedding(detection.data.model_dump_json())
    except Exception:
        embedding = [0.0] * 1024

    data = detection.data
    match detection.type:
        case DetectionType.Decision:
            assert isinstance(data, Decision)
            client.createDecision(
                decision_id=det_id,
                session_id=session_id,
                description=data.description,
                embedding=embedding,
                rationale=data.rationale,
                revisit_trigger=data.revisitTrigger,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Correction:
            assert isinstance(data, Correction)
            client.createCorrection(
                correction_id=det_id,
                session_id=session_id,
                wrong_belief=data.wrongBelief,
                right_belief=data.rightBelief,
                embedding=embedding,
                severity=data.severity.value,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Exception:
            assert isinstance(data, Exception_)
            client.createException(
                exception_id=det_id,
                session_id=session_id,
                rule_broken=data.ruleBroken,
                justification=data.justification,
                embedding=embedding,
                scope=data.scope.value,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Insight:
            assert isinstance(data, Insight)
            client.createInsight(
                insight_id=det_id,
                session_id=session_id,
                category=data.category.value,
                summary=data.summary,
                embedding=embedding,
                implications=data.implications,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Question:
            assert isinstance(data, Question)
            client.createQuestion(
                question_id=det_id,
                session_id=session_id,
                question=data.question,
                answer=data.answer,
                context=data.context,
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.FailedApproach:
            assert isinstance(data, FailedApproach)
            client.createFailedApproach(
                fa_id=det_id,
                session_id=session_id,
                approach=data.approach,
                outcome=data.outcome,
                lesson=data.lesson or "",
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        case DetectionType.Reference:
            assert isinstance(data, ReferenceData)
            for ref in data.references:
                ref_id = f"ref-{uuid.uuid4().hex[:8]}"
                client.createReference(
                    ref_id=ref_id,
                    session_id=session_id,
                    ref_type=ref.type.value,
                    uri=ref.uri,
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
    return True


def handleMessageResponse(session_id: str, transcript_path: str, cwd: str) -> dict:
    user_message, claude_response, context = readTranscript(transcript_path)
    if not user_message:
        return {"detections": 0}

    try:
        detections = asyncio.run(detectAll(user_message, claude_response, context))
    except Exception:
        return {"detections": 0, "error": "detection_failed"}

    if not detections:
        return {"detections": 0}

    client = getClient()
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    stored = 0

    for detection in detections:
        try:
            if _storeDetection(client, session_id, detection):
                stored += 1
        except Exception:
            continue

    client.recordTelemetry(
        event_type="detections",
        project=project,
        data={"count": stored, "types": [d.type.value for d in detections]},
    )

    return {"detections": stored}


def handleSessionEnd(session_id: str, transcript_path: str | None, cwd: str) -> dict:
    client = getClient()
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    clearCurrentSession()

    transcript = ""
    if transcript_path:
        try:
            with open(transcript_path, "r") as f:
                transcript = f.read()
        except Exception:
            pass

    summary = f"Session ended at {datetime.now().isoformat()}"
    if transcript:
        lines = transcript.strip().split("\n")
        summary = f"Session with {len(lines)} message exchanges"

    client.endSession(
        session_id=session_id, transcript=transcript[:100000], summary=summary
    )

    client.recordTelemetry(
        event_type="session_end", project=project, data={"session_id": session_id}
    )

    return {"session_ended": session_id}
