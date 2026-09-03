"""Embedding generation, offloaded to a thread pool (CPU-bound work per requirements).

Default 'local-hash' embedder is a deterministic bag-of-words hashing embedding that
requires no model download, keeping the app runnable fully offline. Swap
EMBEDDING_MODEL=openai to use OpenAI embeddings via httpx.AsyncClient instead.
"""
from __future__ import annotations

import asyncio
import hashlib
import math
import re
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")
_DIMENSIONS = 256


class Embedder(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class LocalHashEmbedder(Embedder):
    """Deterministic, dependency-free embedding suitable for offline dev/tests."""

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_sync, text)

    def _embed_sync(self, text: str) -> list[float]:
        vector = [0.0] * _DIMENSIONS
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % _DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class OpenAIEmbedder(Embedder):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        )

    async def embed(self, text: str) -> list[float]:
        response = await self._client.post(
            "/embeddings", json={"model": "text-embedding-3-small", "input": text}
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


def get_embedder(settings: Settings) -> Embedder:
    if settings.embedding_model.value == "openai":
        return OpenAIEmbedder(settings)
    return LocalHashEmbedder()
