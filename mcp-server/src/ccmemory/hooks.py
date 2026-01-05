import json
import uuid
import asyncio
from datetime import datetime
from typing import Optional

from .graph import getClient
from .detection.detector import detectAll
from .embeddings import getEmbedding


def handleSessionStart(session_id: str, cwd: str) -> dict:
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd
    client = getClient()

    client.createSession(
        session_id=session_id, project=project, started_at=datetime.now().isoformat()
    )

    recent = client.queryRecent(project, limit=15)
    stale = client.queryStaleDecisions(project, days=30)
    failed = client.queryFailedApproaches(project, limit=5)

    context_parts = [f"# Context Graph: {project}", f"Session: {session_id[:12]}...", ""]

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
            context_parts.append(
                f"- {str(d.get('description', ''))[:80]} (developmental, may need revisit)"
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

    return {"context": "\n".join(context_parts), "project": project}


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
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            user_message = str(content)
        elif msg.get("role") == "assistant" and not assistant_response:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            assistant_response = str(content)
        if user_message and assistant_response:
            break

    context = "\n".join(
        f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:200]}" for m in messages[-10:-2]
    )
    return user_message, assistant_response, context


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
        det_id = f"{detection.type}-{uuid.uuid4().hex[:8]}"

        try:
            text_for_embedding = json.dumps(detection.data)
            embedding = getEmbedding(text_for_embedding)
        except Exception:
            embedding = [0.0] * 1024

        try:
            if detection.type == "decision":
                client.createDecision(
                    decision_id=det_id,
                    session_id=session_id,
                    description=detection.data.get("description", ""),
                    embedding=embedding,
                    rationale=detection.data.get("rationale"),
                    revisit_trigger=detection.data.get("revisit_trigger"),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
            elif detection.type == "correction":
                client.createCorrection(
                    correction_id=det_id,
                    session_id=session_id,
                    wrong_belief=detection.data.get("wrong_belief", ""),
                    right_belief=detection.data.get("right_belief", ""),
                    embedding=embedding,
                    severity=detection.data.get("severity"),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
            elif detection.type == "exception":
                client.createException(
                    exception_id=det_id,
                    session_id=session_id,
                    rule_broken=detection.data.get("rule_broken", ""),
                    justification=detection.data.get("justification", ""),
                    embedding=embedding,
                    scope=detection.data.get("scope"),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
            elif detection.type == "insight":
                client.createInsight(
                    insight_id=det_id,
                    session_id=session_id,
                    category=detection.data.get("category", "realization"),
                    summary=detection.data.get("summary", ""),
                    embedding=embedding,
                    implications=detection.data.get("implications"),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
            elif detection.type == "question":
                client.createQuestion(
                    question_id=det_id,
                    session_id=session_id,
                    question=detection.data.get("question", ""),
                    answer=detection.data.get("answer", ""),
                    context=detection.data.get("context"),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
            elif detection.type == "failed_approach":
                client.createFailedApproach(
                    fa_id=det_id,
                    session_id=session_id,
                    approach=detection.data.get("approach", ""),
                    outcome=detection.data.get("outcome", ""),
                    lesson=detection.data.get("lesson", ""),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )
            elif detection.type == "reference":
                for ref in detection.data.get("references", []):
                    ref_id = f"ref-{uuid.uuid4().hex[:8]}"
                    client.createReference(
                        ref_id=ref_id,
                        session_id=session_id,
                        ref_type=ref.get("type", "url"),
                        uri=ref.get("uri", ""),
                        detection_confidence=detection.confidence,
                        detection_method="llm_extraction",
                    )
            stored += 1
        except Exception:
            continue

    client.recordTelemetry(
        event_type="detections",
        project=project,
        data={"count": stored, "types": [d.type for d in detections]},
    )

    return {"detections": stored}


def handleSessionEnd(session_id: str, transcript_path: Optional[str], cwd: str) -> dict:
    client = getClient()
    project = cwd.rsplit("/", 1)[-1] if "/" in cwd else cwd

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

    client.endSession(session_id=session_id, transcript=transcript[:100000], summary=summary)

    client.recordTelemetry(
        event_type="session_end", project=project, data={"session_id": session_id}
    )

    return {"session_ended": session_id}
