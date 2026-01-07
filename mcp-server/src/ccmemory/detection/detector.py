"""LLM-based detection for context capture."""

import logging
import re
import time

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

logger = logging.getLogger("ccmemory.detect")

CONFIDENCE_THRESHOLD = 0.7
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
PATH_PATTERN = re.compile(r'(?:^|[\s"])([~/.]?/[\w./-]+)')


async def detectAll(
    user_message: str, claude_response: str, context: str
) -> list[Detection]:
    if len(user_message.strip()) < 10:
        logger.debug("Skipping detection: user_message too short")
        return []

    logger.info(f"Starting detection on {len(user_message)} char message")
    logger.debug(f"user_message: {user_message[:200]}")
    logger.debug(f"claude_response: {claude_response[:200]}")
    prompt = DETECTION_PROMPT.format(
        context=context[:500],
        claude_response=claude_response[:500],
        user_message=user_message,
    )

    start = time.time()
    logger.debug("Calling LLM for detection...")
    result = await getLlmClient().complete(prompt, DetectionOutput, maxTokens=1000)
    duration = int((time.time() - start) * 1000)
    logger.debug(f"LLM response ({duration}ms): {result.model_dump_json()[:500]}")

    detections = []
    raw_count = 0

    for item in result.decisions:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- decision (conf={item.confidence:.2f}): {item.description[:50]}...")
            detections.append(Detection(type=DetectionType.Decision, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- decision (conf={item.confidence:.2f}): FILTERED")

    for item in result.corrections:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- correction (conf={item.confidence:.2f}): {item.wrong_belief[:50]}...")
            detections.append(Detection(type=DetectionType.Correction, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- correction (conf={item.confidence:.2f}): FILTERED")

    for item in result.exceptions:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- exception (conf={item.confidence:.2f}): {item.rule_broken[:50]}...")
            detections.append(Detection(type=DetectionType.Exception, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- exception (conf={item.confidence:.2f}): FILTERED")

    for item in result.insights:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- insight (conf={item.confidence:.2f}): {item.summary[:50]}...")
            detections.append(Detection(type=DetectionType.Insight, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- insight (conf={item.confidence:.2f}): FILTERED")

    for item in result.questions:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- question (conf={item.confidence:.2f}): {item.question[:50]}...")
            detections.append(Detection(type=DetectionType.Question, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- question (conf={item.confidence:.2f}): FILTERED")

    for item in result.failedApproaches:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- failedApproach (conf={item.confidence:.2f}): {item.approach[:50]}...")
            detections.append(Detection(type=DetectionType.FailedApproach, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- failedApproach (conf={item.confidence:.2f}): FILTERED")

    for item in result.projectFacts:
        raw_count += 1
        if item.confidence >= CONFIDENCE_THRESHOLD:
            logger.debug(f"- projectFact (conf={item.confidence:.2f}): {item.fact[:50]}...")
            detections.append(Detection(type=DetectionType.ProjectFact, confidence=item.confidence, data=item))
        else:
            logger.debug(f"- projectFact (conf={item.confidence:.2f}): FILTERED")

    refs = [Reference(type=ReferenceType.Url, uri=u) for u in URL_PATTERN.findall(user_message)]
    refs += [Reference(type=ReferenceType.FilePath, uri=p) for p in PATH_PATTERN.findall(user_message)]
    if refs:
        logger.debug(f"- references: {len(refs)} found")
        detections.append(Detection(type=DetectionType.Reference, confidence=0.9, data=ReferenceData(references=refs)))

    logger.info(f"Raw: {raw_count} items, after filtering: {len(detections)} detections")
    return detections
