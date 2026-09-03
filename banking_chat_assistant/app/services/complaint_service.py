"""Complaint service: used directly by the /api/v1/complaints REST endpoints
(as opposed to the conversational complaint flow, which goes through the chat agent)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.complaint_agent.agent import ComplaintAgent
from app.core.exceptions import ResourceNotFoundError
from app.db.models import Complaint
from app.events.producer import EventProducer
from app.schemas.agents import ComplaintCategory, ComplaintResponse, ComplaintStatus
from app.schemas.events import EventType


class ComplaintService:
    def __init__(self, session: AsyncSession, producer: EventProducer) -> None:
        self._session = session
        self._producer = producer
        self._agent = ComplaintAgent(session)

    async def create_complaint(
        self, customer_id: str, request_id: str, category: ComplaintCategory, description: str
    ) -> ComplaintResponse:
        complaint = await self._agent.create_complaint_record(customer_id, category, description)

        await self._producer.publish(
            EventType.COMPLAINT_CREATED,
            request_id,
            customer_id=customer_id,
            payload={"complaint_id": complaint.complaint_id, "category": category.value, "escalated": complaint.escalated},
        )

        return ComplaintResponse(
            complaint_id=complaint.complaint_id,
            category=ComplaintCategory(complaint.category),
            status=ComplaintStatus(complaint.status),
            description=complaint.description,
            created_at=complaint.created_at,
            escalated=complaint.escalated,
        )

    async def get_complaint(self, customer_id: str, complaint_id: str) -> ComplaintResponse:
        result = await self._session.execute(
            select(Complaint).where(
                Complaint.complaint_id == complaint_id, Complaint.customer_id == customer_id
            )
        )
        complaint = result.scalar_one_or_none()
        if complaint is None:
            raise ResourceNotFoundError("Complaint not found", {"complaint_id": complaint_id})
        return ComplaintResponse(
            complaint_id=complaint.complaint_id,
            category=ComplaintCategory(complaint.category),
            status=ComplaintStatus(complaint.status),
            description=complaint.description,
            created_at=complaint.created_at,
            escalated=complaint.escalated,
        )
