"""LLM client abstraction. Supports a deterministic 'mock' provider (no external calls,
safe for offline dev/tests) and an OpenAI-compatible provider over httpx.AsyncClient."""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from functools import lru_cache

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> str:
        """Return a raw text completion for the given prompts."""

    async def complete_json(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.0) -> dict:
        """Return a completion that must be valid JSON, validated by the caller with
        Pydantic's model_validate_json()."""
        raw = await self.complete(system_prompt, user_prompt, temperature=temperature)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LLM did not return valid JSON", {"raw": raw}) from exc


class MockLLMClient(LLMClient):
    """Deterministic offline provider used when LLM_PROVIDER=mock (default)."""

    async def complete(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> str:
        return f"[mock-llm] {user_prompt.strip()[:500]}"

    async def complete_json(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.0) -> dict:
        # Deterministic intent classification fallback used by the intent classifier agent.
        seed = int(hashlib.sha256(user_prompt.encode()).hexdigest(), 16)
        return {"_mock_seed": seed}


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def complete(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> str:
        try:
            response = await self._client.post(
                "/chat/completions",
                json={
                    "model": self._settings.llm_model,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("llm_provider_http_error", error=str(exc))
            raise
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMProviderError("Unexpected LLM provider response shape") from exc

    async def aclose(self) -> None:
        await self._client.aclose()


@lru_cache
def get_llm_client_instance(settings: Settings) -> LLMClient:
    if settings.llm_provider.value == "openai":
        return OpenAICompatibleLLMClient(settings)
    return MockLLMClient()
