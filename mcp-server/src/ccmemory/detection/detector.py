"""LLM-based detection for context capture."""

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Optional

from anthropic import AsyncAnthropic

from .prompts import (
    DECISION_PROMPT,
    CORRECTION_PROMPT,
    EXCEPTION_PROMPT,
    INSIGHT_PROMPT,
    QUESTION_PROMPT,
    FAILED_APPROACH_PROMPT,
)

CONFIDENCE_THRESHOLD = 0.7
DETECTION_MODEL = "claude-sonnet-4-20250514"

_client = None


def _getClient():
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


@dataclass
class Detection:
    type: str
    confidence: float
    data: dict


async def detectAll(user_message: str, claude_response: str,
                    context: str) -> list[Detection]:
    """Run all detection prompts in parallel, filter by confidence."""
    if len(user_message.strip()) < 10:
        return []

    tasks = [
        detectDecision(user_message, claude_response, context),
        detectCorrection(user_message, claude_response, context),
        detectException(user_message, claude_response, context),
        detectInsight(user_message, claude_response, context),
        detectQuestion(user_message, claude_response, context),
        detectFailedApproach(user_message, claude_response, context),
        detectReference(user_message),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    detections = []

    for result in results:
        if isinstance(result, Detection) and result.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(result)

    return detections


async def _callDetector(prompt: str) -> dict:
    """Call LLM for classification."""
    client = _getClient()
    response = await client.messages.create(
        model=DETECTION_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text

    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return {}


async def detectDecision(user_message: str, claude_response: str,
                         context: str) -> Optional[Detection]:
    prompt = DECISION_PROMPT.format(
        context=context[:500],
        claude_response=claude_response[:500],
        user_message=user_message
    )
    result = await _callDetector(prompt)
    if result.get("is_decision"):
        return Detection(
            type="decision",
            confidence=result.get("confidence", 0.5),
            data={
                "description": result.get("description", user_message[:200]),
                "rationale": result.get("rationale"),
                "revisit_trigger": result.get("revisit_trigger"),
            }
        )
    return None


async def detectCorrection(user_message: str, claude_response: str,
                           context: str) -> Optional[Detection]:
    prompt = CORRECTION_PROMPT.format(
        claude_response=claude_response[:500],
        user_message=user_message
    )
    result = await _callDetector(prompt)
    if result.get("is_correction"):
        return Detection(
            type="correction",
            confidence=result.get("confidence", 0.5),
            data={
                "wrong_belief": result.get("wrong_belief"),
                "right_belief": result.get("right_belief"),
                "severity": result.get("severity", "significant"),
            }
        )
    return None


async def detectException(user_message: str, claude_response: str,
                          context: str) -> Optional[Detection]:
    prompt = EXCEPTION_PROMPT.format(
        context=context[:500],
        user_message=user_message
    )
    result = await _callDetector(prompt)
    if result.get("is_exception"):
        return Detection(
            type="exception",
            confidence=result.get("confidence", 0.5),
            data={
                "rule_broken": result.get("rule_broken"),
                "justification": result.get("justification"),
                "scope": result.get("scope", "one-time"),
            }
        )
    return None


async def detectInsight(user_message: str, claude_response: str,
                        context: str) -> Optional[Detection]:
    prompt = INSIGHT_PROMPT.format(
        context=context[:500],
        claude_response=claude_response[:500],
        user_message=user_message
    )
    result = await _callDetector(prompt)
    if result.get("is_insight"):
        return Detection(
            type="insight",
            confidence=result.get("confidence", 0.5),
            data={
                "category": result.get("category", "realization"),
                "summary": result.get("summary"),
                "implications": result.get("implications"),
            }
        )
    return None


async def detectQuestion(user_message: str, claude_response: str,
                         context: str) -> Optional[Detection]:
    prompt = QUESTION_PROMPT.format(
        claude_response=claude_response[:500],
        user_message=user_message
    )
    result = await _callDetector(prompt)
    if result.get("is_question"):
        return Detection(
            type="question",
            confidence=result.get("confidence", 0.5),
            data={
                "question": result.get("question"),
                "answer": result.get("answer"),
                "context": result.get("context"),
            }
        )
    return None


async def detectFailedApproach(user_message: str, claude_response: str,
                               context: str) -> Optional[Detection]:
    prompt = FAILED_APPROACH_PROMPT.format(
        context=context[:500],
        user_message=user_message
    )
    result = await _callDetector(prompt)
    if result.get("is_failed_approach"):
        return Detection(
            type="failed_approach",
            confidence=result.get("confidence", 0.5),
            data={
                "approach": result.get("approach"),
                "outcome": result.get("outcome"),
                "lesson": result.get("lesson"),
            }
        )
    return None


async def detectReference(user_message: str) -> Optional[Detection]:
    """Detect URLs and file paths (pattern-based, no LLM needed)."""
    refs = []

    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', user_message)
    for url in urls:
        refs.append({"type": "url", "uri": url})

    paths = re.findall(r'(?:^|[\s"])([~/.]?/[\w./-]+)', user_message)
    for path in paths:
        refs.append({"type": "file_path", "uri": path})

    if refs:
        return Detection(
            type="reference",
            confidence=0.9,
            data={"references": refs}
        )
    return None
