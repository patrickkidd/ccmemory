"""Unit tests for detection prompts."""

import pytest

from ccmemory.detection.prompts import (
    DECISION_PROMPT,
    CORRECTION_PROMPT,
    EXCEPTION_PROMPT,
    INSIGHT_PROMPT,
    QUESTION_PROMPT,
    FAILED_APPROACH_PROMPT,
)


@pytest.mark.unit
def test_decision_prompt_format():
    """Test decision prompt has required placeholders."""
    assert "{context}" in DECISION_PROMPT
    assert "{claude_response}" in DECISION_PROMPT
    assert "{user_message}" in DECISION_PROMPT
    assert "is_decision" in DECISION_PROMPT


@pytest.mark.unit
def test_correction_prompt_format():
    """Test correction prompt has required placeholders."""
    assert "{claude_response}" in CORRECTION_PROMPT
    assert "{user_message}" in CORRECTION_PROMPT
    assert "is_correction" in CORRECTION_PROMPT
    assert "wrong_belief" in CORRECTION_PROMPT
    assert "right_belief" in CORRECTION_PROMPT


@pytest.mark.unit
def test_exception_prompt_format():
    """Test exception prompt has required placeholders."""
    assert "{context}" in EXCEPTION_PROMPT
    assert "{user_message}" in EXCEPTION_PROMPT
    assert "is_exception" in EXCEPTION_PROMPT
    assert "rule_broken" in EXCEPTION_PROMPT


@pytest.mark.unit
def test_insight_prompt_format():
    """Test insight prompt has required placeholders."""
    assert "{context}" in INSIGHT_PROMPT
    assert "{claude_response}" in INSIGHT_PROMPT
    assert "{user_message}" in INSIGHT_PROMPT
    assert "is_insight" in INSIGHT_PROMPT


@pytest.mark.unit
def test_question_prompt_format():
    """Test question prompt has required placeholders."""
    assert "{claude_response}" in QUESTION_PROMPT
    assert "{user_message}" in QUESTION_PROMPT
    assert "is_question" in QUESTION_PROMPT


@pytest.mark.unit
def test_failed_approach_prompt_format():
    """Test failed approach prompt has required placeholders."""
    assert "{context}" in FAILED_APPROACH_PROMPT
    assert "{user_message}" in FAILED_APPROACH_PROMPT
    assert "is_failed_approach" in FAILED_APPROACH_PROMPT


@pytest.mark.unit
def test_prompts_request_json():
    """All prompts should request JSON output."""
    prompts = [
        DECISION_PROMPT,
        CORRECTION_PROMPT,
        EXCEPTION_PROMPT,
        INSIGHT_PROMPT,
        QUESTION_PROMPT,
        FAILED_APPROACH_PROMPT,
    ]
    for prompt in prompts:
        assert "JSON" in prompt or "json" in prompt.lower()
