"""Unit tests for LLM provider abstraction."""

import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_provider_enum():
    from ccmemory.llmprovider import Provider

    assert Provider.Anthropic.value == "anthropic"
    assert Provider.OpenAi.value == "openai"
    assert Provider.Gemini.value == "gemini"


@pytest.mark.unit
def test_models_mapping():
    from ccmemory.llmprovider import MODELS, Provider

    assert Provider.Anthropic in MODELS
    assert Provider.OpenAi in MODELS
    assert Provider.Gemini in MODELS
    assert "claude" in MODELS[Provider.Anthropic]
    assert "gpt" in MODELS[Provider.OpenAi]
    assert "gemini" in MODELS[Provider.Gemini]


@pytest.mark.unit
def test_no_api_key_raises():
    from ccmemory.llmprovider import LlmClient, resetLlmClient

    resetLlmClient()
    env = {
        "ANTHROPIC_API_KEY": "",
        "OPENAI_API_KEY": "",
        "GOOGLE_API_KEY": "",
        "GEMINI_API_KEY": "",
        "CCMEMORY_LLM_PROVIDER": "",
    }
    with patch.dict(os.environ, env, clear=False):
        for key in env:
            os.environ.pop(key, None)
        with pytest.raises(RuntimeError, match="No LLM API key found"):
            LlmClient()


@pytest.mark.unit
def test_explicit_provider_anthropic():
    from ccmemory.llmprovider import LlmClient, Provider, resetLlmClient

    resetLlmClient()
    with patch.dict(
        os.environ,
        {
            "CCMEMORY_LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
        },
    ):
        with patch("anthropic.AsyncAnthropic"):
            client = LlmClient()
            assert client.provider == Provider.Anthropic


@pytest.mark.unit
def test_explicit_provider_openai():
    from ccmemory.llmprovider import LlmClient, Provider, resetLlmClient

    resetLlmClient()
    with patch.dict(
        os.environ,
        {
            "CCMEMORY_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
        },
    ):
        with patch("openai.AsyncOpenAI"):
            client = LlmClient()
            assert client.provider == Provider.OpenAi


@pytest.mark.unit
def test_explicit_provider_gemini():
    from ccmemory.llmprovider import LlmClient, Provider, resetLlmClient

    resetLlmClient()
    with patch.dict(
        os.environ,
        {
            "CCMEMORY_LLM_PROVIDER": "gemini",
            "GOOGLE_API_KEY": "test-key",
        },
    ):
        with patch("google.generativeai.configure"):
            client = LlmClient()
            assert client.provider == Provider.Gemini


@pytest.mark.unit
def test_explicit_provider_missing_key():
    from ccmemory.llmprovider import LlmClient, resetLlmClient

    resetLlmClient()
    with patch.dict(os.environ, {"CCMEMORY_LLM_PROVIDER": "anthropic"}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY required"):
            LlmClient()


@pytest.mark.unit
def test_priority_anthropic_first():
    from ccmemory.llmprovider import LlmClient, Provider, resetLlmClient

    resetLlmClient()
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "anthropic-key",
            "OPENAI_API_KEY": "openai-key",
            "GOOGLE_API_KEY": "google-key",
            "CCMEMORY_LLM_PROVIDER": "",
        },
    ):
        os.environ.pop("CCMEMORY_LLM_PROVIDER", None)
        with patch("anthropic.AsyncAnthropic"):
            client = LlmClient()
            assert client.provider == Provider.Anthropic


@pytest.mark.unit
def test_priority_openai_second():
    from ccmemory.llmprovider import LlmClient, Provider, resetLlmClient

    resetLlmClient()
    with patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "openai-key",
            "GOOGLE_API_KEY": "google-key",
        },
        clear=False,
    ):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("CCMEMORY_LLM_PROVIDER", None)
        with patch("openai.AsyncOpenAI"):
            client = LlmClient()
            assert client.provider == Provider.OpenAi


@pytest.mark.unit
def test_priority_gemini_third():
    from ccmemory.llmprovider import LlmClient, Provider, resetLlmClient

    resetLlmClient()
    with patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "google-key",
        },
        clear=False,
    ):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("CCMEMORY_LLM_PROVIDER", None)
        with patch("google.generativeai.configure"):
            client = LlmClient()
            assert client.provider == Provider.Gemini


@pytest.mark.unit
def test_unknown_provider():
    from ccmemory.llmprovider import LlmClient, resetLlmClient

    resetLlmClient()
    with patch.dict(os.environ, {"CCMEMORY_LLM_PROVIDER": "unknown"}):
        with pytest.raises(RuntimeError, match="Unknown provider"):
            LlmClient()
