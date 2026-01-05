"""Unit tests for LLM-based detection."""

import pytest
import re

from ccmemory.detection.detector import detectReference, Detection


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_reference_url():
    """Test URL detection in user messages."""
    message = "Check out https://example.com/docs for more info"
    result = await detectReference(message)

    assert result is not None
    assert result.type == "reference"
    assert result.confidence == 0.9
    assert len(result.data["references"]) == 1
    assert result.data["references"][0]["type"] == "url"
    assert result.data["references"][0]["uri"] == "https://example.com/docs"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_reference_multiple_urls():
    """Test multiple URL detection."""
    message = "See https://docs.python.org and https://flask.palletsprojects.com"
    result = await detectReference(message)

    assert result is not None
    assert len(result.data["references"]) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_reference_file_path():
    """Test file path detection."""
    message = "The config is in /etc/myapp/config.yaml"
    result = await detectReference(message)

    assert result is not None
    assert any(r["type"] == "file_path" for r in result.data["references"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_reference_no_references():
    """Test when no references are present."""
    message = "Just a regular message with no links"
    result = await detectReference(message)

    assert result is None


@pytest.mark.unit
def test_detection_dataclass():
    """Test Detection dataclass."""
    detection = Detection(
        type="decision",
        confidence=0.85,
        data={"description": "Test decision"}
    )

    assert detection.type == "decision"
    assert detection.confidence == 0.85
    assert detection.data["description"] == "Test decision"
