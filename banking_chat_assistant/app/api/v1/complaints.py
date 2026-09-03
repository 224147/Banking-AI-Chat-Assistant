"""Complaint endpoints. Creation is idempotency-key protected."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.clients.broker_client import BrokerClient
from app.core.dependencies import get_broker_client, get_current_customer, get_db_session
from app.core.idempotency import get_cached_response, store_response
from app.events.producer import EventProducer
from app.schemas.agents import ComplaintRequest, ComplaintResponse
from app.schemas.customer import AuthenticatedCustomer
from app.services.complaint_service import ComplaintService
from app.services.chat_service import new_request_id

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintResponse)
async def create_complaint(
    complaint_request: ComplaintRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
    broker_client: BrokerClient = Depends(get_broker_client),
) -> ComplaintResponse:
    cached = await get_cached_response(session, idempotency_key, customer.customer_id)
    if cached is not None:
        return ComplaintResponse(**cached)

    request_id = getattr(request.state, "request_id", new_request_id())
    producer = EventProducer(broker_client)
    service = ComplaintService(session, producer)
    response = await service.create_complaint(
        customer.customer_id, request_id, complaint_request.category, complaint_request.description
    )
    await store_response(session, idempotency_key, customer.customer_id, response.model_dump(mode="json"))
    return response


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: str,
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
    broker_client: BrokerClient = Depends(get_broker_client),
) -> ComplaintResponse:
    producer = EventProducer(broker_client)
    service = ComplaintService(session, producer)
    return await service.get_complaint(customer.customer_id, complaint_id)
