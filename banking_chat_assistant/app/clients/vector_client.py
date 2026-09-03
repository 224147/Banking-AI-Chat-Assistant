"""ChromaDB vector store client. Blocking chromadb calls are offloaded to a thread pool."""
from __future__ import annotations

import asyncio
from functools import lru_cache

import chromadb

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "banking_knowledge_base"


class VectorClient:
    def __init__(self, settings: Settings) -> None:
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collection = self._client.get_or_create_collection(COLLECTION_NAME)

    async def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> None:
        await asyncio.to_thread(
            self._collection.upsert, ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    async def query(self, query_embedding: list[float], top_k: int) -> dict:
        return await asyncio.to_thread(
            self._collection.query, query_embeddings=[query_embedding], n_results=top_k
        )

    async def count(self) -> int:
        return await asyncio.to_thread(self._collection.count)


@lru_cache
def get_vector_client_instance(settings: Settings) -> VectorClient:
    return VectorClient(settings)
