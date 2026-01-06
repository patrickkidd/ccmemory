"""LLM-based detection for context capture."""

import re

from ccmemory.llmprovider import getLlmClient
from .prompts import DETECTION_PROMPT
from .schemas import (
    Detection,
    DetectionOutput,
    DetectionType,
    Reference,
    ReferenceData,
    ReferenceType,
)

CONFIDENCE_THRESHOLD = 0.7
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
PATH_PATTERN = re.compile(r'(?:^|[\s"])([~/.]?/[\w./-]+)')


async def detectAll(
    user_message: str, claude_response: str, context: str
) -> list[Detection]:
    if len(user_message.strip()) < 10:
        return []

    prompt = DETECTION_PROMPT.format(
        context=context[:500],
        claude_response=claude_response[:500],
        user_message=user_message,
    )
    result = await getLlmClient().complete(prompt, DetectionOutput, maxTokens=1000)

    detections = []
    for item in result.decisions:
        if item.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(Detection(type=DetectionType.Decision, confidence=item.confidence, data=item))
    for item in result.corrections:
        if item.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(Detection(type=DetectionType.Correction, confidence=item.confidence, data=item))
    for item in result.exceptions:
        if item.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(Detection(type=DetectionType.Exception, confidence=item.confidence, data=item))
    for item in result.insights:
        if item.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(Detection(type=DetectionType.Insight, confidence=item.confidence, data=item))
    for item in result.questions:
        if item.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(Detection(type=DetectionType.Question, confidence=item.confidence, data=item))
    for item in result.failedApproaches:
        if item.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(Detection(type=DetectionType.FailedApproach, confidence=item.confidence, data=item))

    refs = [Reference(type=ReferenceType.Url, uri=u) for u in URL_PATTERN.findall(user_message)]
    refs += [Reference(type=ReferenceType.FilePath, uri=p) for p in PATH_PATTERN.findall(user_message)]
    if refs:
        detections.append(Detection(type=DetectionType.Reference, confidence=0.9, data=ReferenceData(references=refs)))

    return detections
