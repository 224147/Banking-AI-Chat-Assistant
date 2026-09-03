"""Service-layer tests with mocked broker (degraded mode) and a real sqlite session."""
import uuid

import pytest

from app.clients.broker_client import BrokerClient
from app.clients.banking_api_client import BankingAPIClient
from app.clients.vector_client import get_vector_client_instance
from app.core.config import get_settings
from app.core.exceptions import ResourceNotFoundError
from app.core.idempotency import get_cached_response, store_response
from app.db.seed import DEMO_CUSTOMER_ID
from app.db.session import get_session_factory
from app.events.producer import EventProducer
from app.rag.embeddings.embedder import get_embedder
from app.rag.retrieval.retriever import Retriever
from app.rag.vectordb.chroma_store import ChromaStore
from app.schemas.events import EventType
from app.services.audit_service import AuditService
from app.services.rag_service import RAGService


class _StubBroker:
    def __init__(self) -> None:
        self.published = []

    async def publish(self, event) -> None:
        self.published.append(event)


@pytest.fixture
def session_factory():
    return get_session_factory(get_settings())


@pytest.mark.asyncio
async def test_audit_service_persists_and_publishes(session_factory, _bootstrap_test_environment):
    broker = _StubBroker()
    async with session_factory() as session:
        service = AuditService(session, EventProducer(broker))
        await service.record(
            EventType.INTENT_CLASSIFIED, "req-1", session_id="s1", customer_id=DEMO_CUSTOMER_ID, payload={"intent": "FAQ"}
        )
    assert len(broker.published) == 1
    assert broker.published[0].event_type == EventType.AUDIT_LOGGED


@pytest.mark.asyncio
async def test_rag_service_search_returns_citations(_bootstrap_test_environment):
    settings = get_settings()
    store = ChromaStore(get_vector_client_instance(settings), get_embedder(settings))
    service = RAGService(store, Retriever(store, settings))
    context = await service.search("savings account minimum balance policy")
    assert context.documents
    assert context.average_confidence > 0


@pytest.mark.asyncio
async def test_idempotency_cache_roundtrip(session_factory, _bootstrap_test_environment):
    key = f"unit-key-{uuid.uuid4()}"
    async with session_factory() as session:
        assert await get_cached_response(session, key, DEMO_CUSTOMER_ID) is None
        await store_response(session, key, DEMO_CUSTOMER_ID, {"ok": True})
        assert await get_cached_response(session, key, DEMO_CUSTOMER_ID) == {"ok": True}


@pytest.mark.asyncio
async def test_banking_client_raises_for_unknown_loan(session_factory, _bootstrap_test_environment):
    async with session_factory() as session:
        client = BankingAPIClient(session)
        with pytest.raises(ResourceNotFoundError):
            await client.get_loan(DEMO_CUSTOMER_ID, "no-such-loan")


@pytest.mark.asyncio
async def test_broker_publish_is_noop_when_disabled():
    broker = BrokerClient(get_settings())
    assert broker.enabled is False
    producer = EventProducer(broker)
    await producer.publish(EventType.TOOL_EXECUTED, "req-2")  # must not raise
