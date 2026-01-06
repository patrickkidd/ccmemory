"""Multi-provider LLM abstraction with structured outputs."""

import os
from enum import Enum
from typing import TypeVar

from pydantic import BaseModel


class Provider(Enum):
    Anthropic = "anthropic"
    OpenAi = "openai"
    Gemini = "gemini"


MODELS = {
    Provider.Anthropic: "claude-sonnet-4-20250514",
    Provider.OpenAi: "gpt-4o-mini",
    Provider.Gemini: "gemini-2.0-flash",
}

T = TypeVar("T", bound=BaseModel)

_client = None


class LlmClient:
    def __init__(self):
        self._provider: Provider | None = None
        self._client = None
        self._init()

    def _init(self):
        explicit = os.getenv("CCMEMORY_LLM_PROVIDER", "").lower()
        if explicit:
            if explicit == "anthropic":
                self._initAnthropic()
            elif explicit == "openai":
                self._initOpenAi()
            elif explicit == "gemini":
                self._initGemini()
            else:
                raise RuntimeError(f"Unknown provider: {explicit}")
            return

        if os.getenv("ANTHROPIC_API_KEY"):
            self._initAnthropic()
        elif os.getenv("OPENAI_API_KEY"):
            self._initOpenAi()
        elif os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            self._initGemini()
        else:
            raise RuntimeError(
                "No LLM API key found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
            )

    def _initAnthropic(self):
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY required for anthropic provider")
        from anthropic import AsyncAnthropic

        self._provider = Provider.Anthropic
        self._client = AsyncAnthropic()

    def _initOpenAi(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY required for openai provider")
        from openai import AsyncOpenAI

        self._provider = Provider.OpenAi
        self._client = AsyncOpenAI()

    def _initGemini(self):
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY required for gemini provider")
        from google import genai

        self._provider = Provider.Gemini
        self._client = genai.Client(api_key=key)

    @property
    def provider(self) -> Provider:
        return self._provider

    async def complete(self, prompt: str, schema: type[T], maxTokens: int = 500) -> T:
        model = MODELS[self._provider]

        if self._provider == Provider.Anthropic:
            return await self._completeAnthropic(prompt, schema, model, maxTokens)
        elif self._provider == Provider.OpenAi:
            return await self._completeOpenAi(prompt, schema, model, maxTokens)
        elif self._provider == Provider.Gemini:
            return await self._completeGemini(prompt, schema, model, maxTokens)

    async def _completeAnthropic(
        self, prompt: str, schema: type[T], model: str, maxTokens: int
    ) -> T:
        import json

        response = await self._client.messages.create(
            model=model,
            max_tokens=maxTokens,
            messages=[{"role": "user", "content": prompt}],
            extra_headers={"anthropic-beta": "structured-outputs-2025-11-13"},
            output_format={
                "type": "json",
                "schema": schema.model_json_schema(),
            },
        )
        text = response.content[0].text
        return schema.model_validate(json.loads(text))

    async def _completeOpenAi(
        self, prompt: str, schema: type[T], model: str, maxTokens: int
    ) -> T:
        import json

        response = await self._client.chat.completions.create(
            model=model,
            max_tokens=maxTokens,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": schema.model_json_schema(),
                },
            },
        )
        text = response.choices[0].message.content
        return schema.model_validate(json.loads(text))

    async def _completeGemini(
        self, prompt: str, schema: type[T], model: str, maxTokens: int
    ) -> T:
        import asyncio
        from google.genai import types

        def generate():
            return self._client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=maxTokens,
                ),
            )

        response = await asyncio.to_thread(generate)
        return schema.model_validate_json(response.text)


def getLlmClient() -> LlmClient:
    global _client
    if _client is None:
        _client = LlmClient()
    return _client


def resetLlmClient():
    global _client
    _client = None
