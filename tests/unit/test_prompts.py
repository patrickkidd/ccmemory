"""Unit tests for detection prompt."""

import pytest

from ccmemory.detection.prompts import DETECTION_PROMPT


@pytest.mark.unit
def test_prompt_placeholders():
    assert "{context}" in DETECTION_PROMPT
    assert "{claude_response}" in DETECTION_PROMPT
    assert "{user_message}" in DETECTION_PROMPT


@pytest.mark.unit
def test_prompt_detection_types():
    assert "DECISION" in DETECTION_PROMPT
    assert "CORRECTION" in DETECTION_PROMPT
    assert "EXCEPTION" in DETECTION_PROMPT
    assert "INSIGHT" in DETECTION_PROMPT
    assert "QUESTION" in DETECTION_PROMPT
    assert "FAILED_APPROACH" in DETECTION_PROMPT


@pytest.mark.unit
def test_prompt_requests_json():
    assert "JSON" in DETECTION_PROMPT


@pytest.mark.unit
def test_prompt_has_examples():
    assert "CORRECT" in DETECTION_PROMPT
    assert "WRONG" in DETECTION_PROMPT


@pytest.mark.unit
def test_prompt_formattable():
    formatted = DETECTION_PROMPT.format(
        context="test context",
        claude_response="test response",
        user_message="test message",
    )
    assert "test context" in formatted
    assert "test response" in formatted
    assert "test message" in formatted
