"""Shared pytest fixtures. Configures a self-contained (sqlite + mock-LLM + degraded
broker) test environment so the suite runs fully offline without external services."""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{tempfile.gettempdir()}/banking_test.db")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("SESSION_SECRET_KEY", "test-secret-key")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_MODEL", "local-hash")
os.environ.setdefault("CHROMA_PERSIST_DIR", f"{tempfile.gettempdir()}/banking_test_chroma")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.clients.vector_client import get_vector_client_instance
from app.core.config import get_settings
from app.core.dependencies import get_current_customer
from app.db.seed import DEMO_CUSTOMER_ID, seed_demo_data
from app.db.session import get_session_factory, init_models
from app.rag.embeddings.embedder import get_embedder
from app.rag.ingestion.ingest import ingest_seed_documents
from app.rag.vectordb.chroma_store import ChromaStore
from app.schemas.customer import AuthenticatedCustomer
from main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _bootstrap_test_environment():
    settings = get_settings()
    # Start from a clean database so tests (idempotency keys in particular) are repeatable.
    db_path = settings.database_url.split("///")[-1]
    if os.path.exists(db_path):
        os.remove(db_path)

    await init_models(settings)
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        await seed_demo_data(session)

    store = ChromaStore(get_vector_client_instance(settings), get_embedder(settings))
    await ingest_seed_documents(store)
    yield


@pytest_asyncio.fixture
async def client(_bootstrap_test_environment):
    app.dependency_overrides[get_current_customer] = lambda: AuthenticatedCustomer(customer_id=DEMO_CUSTOMER_ID)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
def demo_customer_id() -> str:
    return DEMO_CUSTOMER_ID

