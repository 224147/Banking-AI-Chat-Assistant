"""Card service endpoints. Block/unblock are idempotency-key protected."""
from fastapi import APIRouter, Depends, Header

from app.clients.banking_api_client import BankingAPIClient
from app.clients.broker_client import BrokerClient
from app.core.dependencies import get_banking_api_client, get_broker_client, get_current_customer, get_db_session
from app.core.idempotency import get_cached_response, store_response
from app.events.producer import EventProducer
from app.schemas.agents import CardRequest, CardResponse
from app.schemas.customer import AuthenticatedCustomer
from app.schemas.events import EventType
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


async def _set_status(
    card_request: CardRequest,
    customer: AuthenticatedCustomer,
    banking_client: BankingAPIClient,
    session: AsyncSession,
    broker_client: BrokerClient,
    idempotency_key: str,
    status: str,
    event_type: EventType,
) -> CardResponse:
    cached = await get_cached_response(session, idempotency_key, customer.customer_id)
    if cached is not None:
        return CardResponse(**cached)

    card = await banking_client.set_card_status(customer.customer_id, card_request.card_id, status)
    response = CardResponse(
        card_id=card.card_id,
        card_type=card.card_type,
        status=card.status,
        card_number_masked=BankingAPIClient.mask_card_number(card.card_number),
    )
    await store_response(session, idempotency_key, customer.customer_id, response.model_dump(mode="json"))

    producer = EventProducer(broker_client)
    await producer.publish(event_type, idempotency_key, customer_id=customer.customer_id, payload={"card_id": card.card_id})
    return response


@router.post("/block", response_model=CardResponse)
async def block_card(
    card_request: CardRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    banking_client: BankingAPIClient = Depends(get_banking_api_client),
    session: AsyncSession = Depends(get_db_session),
    broker_client: BrokerClient = Depends(get_broker_client),
) -> CardResponse:
    return await _set_status(
        card_request, customer, banking_client, session, broker_client, idempotency_key, "BLOCKED", EventType.CARD_BLOCKED
    )


@router.post("/unblock", response_model=CardResponse)
async def unblock_card(
    card_request: CardRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    banking_client: BankingAPIClient = Depends(get_banking_api_client),
    session: AsyncSession = Depends(get_db_session),
    broker_client: BrokerClient = Depends(get_broker_client),
) -> CardResponse:
    return await _set_status(
        card_request, customer, banking_client, session, broker_client, idempotency_key, "ACTIVE", EventType.CARD_UNBLOCKED
    )
