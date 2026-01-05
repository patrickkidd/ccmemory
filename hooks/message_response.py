#!/usr/bin/env python3
"""Stop hook - detect and capture context after Claude finishes responding.

The Stop hook fires after every Claude response (not just tool calls), making it
ideal for detecting decisions, corrections, and insights from user messages.

Claude Code provides via stdin for Stop:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "Stop"
}

We read the transcript file to get the full conversation context for detection.
"""

import json
import os
import sys
import uuid
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from ccmemory.graph import getClient
from ccmemory.detection.detector import detectAll
from ccmemory.embeddings import getEmbedding


def readTranscript(transcript_path: str) -> tuple[str, str, str]:
    """Read transcript to extract recent user message and context."""
    if not os.path.exists(transcript_path):
        return "", "", ""

    messages = []
    with open(transcript_path, 'r') as f:
        for line in f:
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue

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


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    session_id = input_data.get("session_id")
    transcript_path = input_data.get("transcript_path")

    if not session_id or not transcript_path:
        return

    user_message, claude_response, context = readTranscript(transcript_path)

    if not user_message:
        return

    try:
        detections = asyncio.run(detectAll(user_message, claude_response, context))
    except Exception:
        return

    if not detections:
        return

    try:
        client = getClient()
    except Exception:
        return

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
        except Exception:
            continue

    try:
        client.recordTelemetry(
            event_type="detections",
            project=os.path.basename(os.getcwd()),
            data={"count": len(detections), "types": [d.type for d in detections]}
        )
    except Exception:
        pass

    print(json.dumps({"detections": len(detections)}))


if __name__ == "__main__":
    main()
