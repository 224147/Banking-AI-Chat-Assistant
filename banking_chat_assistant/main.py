"""Application entrypoint. Kept minimal: wiring only, no business logic."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, cards, chat, complaints, customer, health, loans
from app.clients.broker_client import BrokerClient
from app.clients.vector_client import get_vector_client_instance
from app.core.config import get_settings
from app.core.exceptions import BankingAssistantError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.telemetry import configure_telemetry
from app.db.seed import seed_demo_data
from app.db.session import get_session_factory, init_models
from app.events.consumer import start_consumers
from app.rag.embeddings.embedder import get_embedder
from app.rag.ingestion.ingest import ingest_seed_documents
from app.rag.vectordb.chroma_store import ChromaStore
from app.schemas.errors import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.debug)

    await init_models(settings)
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        await seed_demo_data(session)

    vector_client = get_vector_client_instance(settings)
    store = ChromaStore(vector_client, get_embedder(settings))
    await ingest_seed_documents(store)

    broker_client = BrokerClient.get_instance(settings)
    await broker_client.connect()
    await start_consumers(broker_client, settings)

    logger.info("application_startup_complete", environment=settings.environment)
    yield

    await broker_client.close()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )
    configure_telemetry(app, settings)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(customer.router)
    app.include_router(cards.router)
    app.include_router(loans.router)
    app.include_router(complaints.router)

    @app.exception_handler(BankingAssistantError)
    async def handle_banking_assistant_error(_request: Request, exc: BankingAssistantError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error_code=exc.error_code, message=exc.message, details=exc.details).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error_code="INTERNAL_ERROR", message="An unexpected error occurred.").model_dump(),
        )

    return app


app = create_app()
