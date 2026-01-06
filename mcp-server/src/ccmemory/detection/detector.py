"""LLM-based detection for context capture."""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional

from ccmemory.llmprovider import getLlmClient
from .prompts import (
    DECISION_PROMPT,
    CORRECTION_PROMPT,
    EXCEPTION_PROMPT,
    INSIGHT_PROMPT,
    QUESTION_PROMPT,
    FAILED_APPROACH_PROMPT,
)
from .schemas import (
    DecisionResult,
    CorrectionResult,
    ExceptionResult,
    InsightResult,
    QuestionResult,
    FailedApproachResult,
)

CONFIDENCE_THRESHOLD = 0.7


@dataclass
class Detection:
    type: str
    confidence: float
    data: dict


async def detectAll(
    user_message: str, claude_response: str, context: str
) -> list[Detection]:
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


async def detectDecision(
    user_message: str, claude_response: str, context: str
) -> Optional[Detection]:
    prompt = DECISION_PROMPT.format(
        context=context[:500],
        claude_response=claude_response[:500],
        user_message=user_message,
    )
    client = getLlmClient()
    result = await client.complete(prompt, DecisionResult, maxTokens=500)
    if result.isDecision:
        return Detection(
            type="decision",
            confidence=result.confidence,
            data={
                "description": result.description or user_message[:200],
                "rationale": result.rationale,
                "revisit_trigger": result.revisitTrigger,
            },
        )
    return None


async def detectCorrection(
    user_message: str, claude_response: str, context: str
) -> Optional[Detection]:
    prompt = CORRECTION_PROMPT.format(
        claude_response=claude_response[:500], user_message=user_message
    )
    client = getLlmClient()
    result = await client.complete(prompt, CorrectionResult, maxTokens=500)
    if result.isCorrection:
        return Detection(
            type="correction",
            confidence=result.confidence,
            data={
                "wrong_belief": result.wrongBelief,
                "right_belief": result.rightBelief,
                "severity": result.severity or "significant",
            },
        )
    return None


async def detectException(
    user_message: str, claude_response: str, context: str
) -> Optional[Detection]:
    prompt = EXCEPTION_PROMPT.format(context=context[:500], user_message=user_message)
    client = getLlmClient()
    result = await client.complete(prompt, ExceptionResult, maxTokens=500)
    if result.isException:
        return Detection(
            type="exception",
            confidence=result.confidence,
            data={
                "rule_broken": result.ruleBroken,
                "justification": result.justification,
                "scope": result.scope or "one-time",
            },
        )
    return None


async def detectInsight(
    user_message: str, claude_response: str, context: str
) -> Optional[Detection]:
    prompt = INSIGHT_PROMPT.format(
        context=context[:500],
        claude_response=claude_response[:500],
        user_message=user_message,
    )
    client = getLlmClient()
    result = await client.complete(prompt, InsightResult, maxTokens=500)
    if result.isInsight:
        return Detection(
            type="insight",
            confidence=result.confidence,
            data={
                "category": result.category or "realization",
                "summary": result.summary,
                "implications": result.implications,
            },
        )
    return None


async def detectQuestion(
    user_message: str, claude_response: str, context: str
) -> Optional[Detection]:
    prompt = QUESTION_PROMPT.format(
        claude_response=claude_response[:500], user_message=user_message
    )
    client = getLlmClient()
    result = await client.complete(prompt, QuestionResult, maxTokens=500)
    if result.isQuestion:
        return Detection(
            type="question",
            confidence=result.confidence,
            data={
                "question": result.question,
                "answer": result.answer,
                "context": result.context,
            },
        )
    return None


async def detectFailedApproach(
    user_message: str, claude_response: str, context: str
) -> Optional[Detection]:
    prompt = FAILED_APPROACH_PROMPT.format(
        context=context[:500], user_message=user_message
    )
    client = getLlmClient()
    result = await client.complete(prompt, FailedApproachResult, maxTokens=500)
    if result.isFailedApproach:
        return Detection(
            type="failed_approach",
            confidence=result.confidence,
            data={
                "approach": result.approach,
                "outcome": result.outcome,
                "lesson": result.lesson,
            },
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
        return Detection(type="reference", confidence=0.9, data={"references": refs})
    return None
