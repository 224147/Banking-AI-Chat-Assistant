"""FastAPI dependency providers. All external clients are injected for testability
via app.dependency_overrides."""
from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.banking_api_client import BankingAPIClient
from app.clients.broker_client import BrokerClient
from app.clients.llm_client import LLMClient, get_llm_client_instance
from app.clients.vector_client import VectorClient, get_vector_client_instance
from app.core.config import Settings, get_settings
from app.core.security import verify_session_token
from app.db.session import get_session_factory
from app.schemas.customer import AuthenticatedCustomer


def get_app_settings() -> Settings:
    return get_settings()


async def get_db_session(
    settings: Settings = Depends(get_app_settings),
) -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        yield session


def get_llm_client(settings: Settings = Depends(get_app_settings)) -> LLMClient:
    return get_llm_client_instance(settings)


def get_vector_client(settings: Settings = Depends(get_app_settings)) -> VectorClient:
    return get_vector_client_instance(settings)


def get_broker_client(settings: Settings = Depends(get_app_settings)) -> BrokerClient:
    return BrokerClient.get_instance(settings)


def get_banking_api_client(
    db_session: AsyncSession = Depends(get_db_session),
) -> BankingAPIClient:
    return BankingAPIClient(db_session)


async def get_current_customer(
    authorization: str = Header(..., description="Bearer session token"),
    settings: Settings = Depends(get_app_settings),
) -> AuthenticatedCustomer:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        from app.core.exceptions import AuthenticationError

        raise AuthenticationError("Missing or malformed Authorization header")
    customer_id = verify_session_token(token, settings)
    return AuthenticatedCustomer(customer_id=customer_id)
