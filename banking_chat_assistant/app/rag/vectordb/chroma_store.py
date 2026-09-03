"""Thin wrapper tying the VectorClient (ChromaDB) to embedding generation."""
from app.clients.vector_client import VectorClient
from app.rag.embeddings.embedder import Embedder


class ChromaStore:
    def __init__(self, vector_client: VectorClient, embedder: Embedder) -> None:
        self._vector_client = vector_client
        self._embedder = embedder

    async def index_documents(self, documents: list[dict]) -> None:
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        embeddings = await self._embedder.embed_batch(texts)
        await self._vector_client.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    async def search(self, query: str, top_k: int) -> list[dict]:
        query_embedding = await self._embedder.embed(query)
        raw = await self._vector_client.query(query_embedding, top_k)
        results = []
        ids = raw.get("ids", [[]])[0]
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            score = max(0.0, 1.0 - distance / 2.0)  # cosine distance -> similarity score
            results.append({"id": doc_id, "text": document, "metadata": metadata, "score": score})
        return results
