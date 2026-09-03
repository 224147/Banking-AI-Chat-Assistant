"""Chat endpoint: single entry point into the multi-agent orchestrator."""
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.clients.broker_client import BrokerClient
from app.clients.llm_client import LLMClient
from app.clients.vector_client import VectorClient
from app.core.config import Settings
from app.core.dependencies import (
    get_app_settings,
    get_broker_client,
    get_current_customer,
    get_db_session,
    get_llm_client,
    get_vector_client,
)
from app.events.producer import EventProducer
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.customer import AuthenticatedCustomer
from app.services.chat_service import ChatService, new_request_id

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    request: Request,
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
    llm_client: LLMClient = Depends(get_llm_client),
    vector_client: VectorClient = Depends(get_vector_client),
    broker_client: BrokerClient = Depends(get_broker_client),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    request_id = getattr(request.state, "request_id", new_request_id())
    producer = EventProducer(broker_client)
    service = ChatService(session, llm_client, vector_client, settings, producer)
    return await service.handle_chat(customer.customer_id, request_id, chat_request)


@router.post("/stream")
async def chat_stream(
    chat_request: ChatRequest,
    request: Request,
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db_session),
    llm_client: LLMClient = Depends(get_llm_client),
    vector_client: VectorClient = Depends(get_vector_client),
    broker_client: BrokerClient = Depends(get_broker_client),
    settings: Settings = Depends(get_app_settings),
) -> StreamingResponse:
    """Server-Sent Events token stream. Runs the full workflow, then streams the
    resulting reply in chunks (works uniformly for both mock and real LLM providers)."""
    request_id = getattr(request.state, "request_id", new_request_id())
    producer = EventProducer(broker_client)
    service = ChatService(session, llm_client, vector_client, settings, producer)
    response = await service.handle_chat(customer.customer_id, request_id, chat_request)

    async def event_generator():
        for i in range(0, len(response.reply), 20):
            chunk = response.reply[i : i + 20]
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True, 'citations': [c.model_dump() for c in response.citations]})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
