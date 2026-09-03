"""Retrieval flow: embedding -> vector search -> reranking -> confidence-scored context."""
from app.core.config import Settings
from app.rag.reranking.reranker import rerank
from app.rag.vectordb.chroma_store import ChromaStore
from app.schemas.chat import RetrievalContext, SourceCitation


class Retriever:
    def __init__(self, store: ChromaStore, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    async def retrieve(self, query: str) -> RetrievalContext:
        candidates = await self._store.search(query, top_k=self._settings.top_k * 2)
        reranked = await rerank(query, candidates)
        top = reranked[: self._settings.top_k]
        filtered = [c for c in top if c["score"] >= self._settings.similarity_threshold]

        citations = [
            SourceCitation(
                document_id=c["id"],
                title=c["metadata"].get("title", c["id"]),
                snippet=c["text"][:280],
                score=round(c["score"], 4),
            )
            for c in filtered
        ]
        avg_confidence = sum(c.score for c in citations) / len(citations) if citations else 0.0
        return RetrievalContext(query=query, documents=citations, average_confidence=avg_confidence)
