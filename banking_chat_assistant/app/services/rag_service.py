"""RAG service: exposes retrieval-augmented answers outside of the chat orchestrator
(e.g. for direct FAQ endpoints or ingestion triggers)."""
from app.rag.ingestion.ingest import ingest_seed_documents
from app.rag.retrieval.retriever import Retriever
from app.rag.vectordb.chroma_store import ChromaStore
from app.schemas.chat import RetrievalContext


class RAGService:
    def __init__(self, store: ChromaStore, retriever: Retriever) -> None:
        self._store = store
        self._retriever = retriever

    async def ensure_seed_data(self) -> None:
        await ingest_seed_documents(self._store)

    async def search(self, query: str) -> RetrievalContext:
        return await self._retriever.retrieve(query)
