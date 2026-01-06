"""Unit tests for LLM-based detection."""

import pytest

from ccmemory.detection.detector import URL_PATTERN, PATH_PATTERN
from ccmemory.detection.schemas import (
    Decision,
    Detection,
    DetectionType,
    Reference,
    ReferenceData,
    ReferenceType,
)


@pytest.mark.unit
def test_url_pattern():
    message = "Check out https://example.com/docs for more info"
    urls = URL_PATTERN.findall(message)
    assert urls == ["https://example.com/docs"]


@pytest.mark.unit
def test_url_pattern_multiple():
    message = "See https://docs.python.org and https://flask.palletsprojects.com"
    urls = URL_PATTERN.findall(message)
    assert len(urls) == 2


@pytest.mark.unit
def test_path_pattern():
    message = "The config is in /etc/myapp/config.yaml"
    paths = PATH_PATTERN.findall(message)
    assert any("/etc/myapp/config.yaml" in p for p in paths)


@pytest.mark.unit
def test_url_pattern_no_match():
    message = "Just a regular message with no links"
    urls = URL_PATTERN.findall(message)
    assert urls == []


@pytest.mark.unit
def test_detection_model():
    detection = Detection(
        type=DetectionType.Decision,
        confidence=0.85,
        data=Decision(confidence=0.85, description="Test decision"),
    )
    assert detection.type == DetectionType.Decision
    assert detection.confidence == 0.85
    assert isinstance(detection.data, Decision)
    assert detection.data.description == "Test decision"


@pytest.mark.unit
def test_reference_model():
    ref = Reference(type=ReferenceType.Url, uri="https://example.com")
    assert ref.type == ReferenceType.Url
    assert ref.uri == "https://example.com"


@pytest.mark.unit
def test_reference_data_model():
    refs = ReferenceData(
        references=[
            Reference(type=ReferenceType.Url, uri="https://example.com"),
            Reference(type=ReferenceType.FilePath, uri="/etc/config.yaml"),
        ]
    )
    assert len(refs.references) == 2
    assert refs.references[0].type == ReferenceType.Url
    assert refs.references[1].type == ReferenceType.FilePath
