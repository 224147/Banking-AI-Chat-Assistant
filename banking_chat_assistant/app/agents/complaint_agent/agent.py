"""Complaint agent: registration, status lookup, escalation."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.db.models import Complaint
from app.schemas.agents import ComplaintCategory
from app.schemas.chat import AgentContext, AgentResponse, IntentType

_ESCALATION_KEYWORDS = ("urgent", "immediately", "escalate", "fraud", "unauthorized")


class ComplaintAgent:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_complaint_record(
        self, customer_id: str, category: ComplaintCategory, description: str
    ) -> Complaint:
        escalated = any(keyword in description.lower() for keyword in _ESCALATION_KEYWORDS)
        complaint = Complaint(
            complaint_id=str(uuid.uuid4()),
            customer_id=customer_id,
            category=category.value,
            description=description,
            status="ESCALATED" if escalated else "OPEN",
            escalated=escalated,
            created_at=datetime.utcnow(),
        )
        self._session.add(complaint)
        await self._session.commit()
        await self._session.refresh(complaint)
        return complaint

    async def raise_complaint(
        self, context: AgentContext, category: ComplaintCategory, description: str
    ) -> AgentResponse:
        complaint = await self.create_complaint_record(context.customer_id, category, description)

        reply = f"Your complaint has been registered with ID {complaint.complaint_id}."
        if complaint.escalated:
            reply += " Given the nature of your issue, it has been escalated to a specialist team."
        return AgentResponse(
            agent_name="complaint_agent",
            intent=IntentType.COMPLAINT,
            reply=reply,
            confidence=1.0,
            tool_calls=["create_complaint"],
        )

    async def get_status(self, context: AgentContext, complaint_id: str) -> AgentResponse:
        result = await self._session.execute(
            select(Complaint).where(
                Complaint.complaint_id == complaint_id, Complaint.customer_id == context.customer_id
            )
        )
        complaint = result.scalar_one_or_none()
        if complaint is None:
            raise ResourceNotFoundError("Complaint not found", {"complaint_id": complaint_id})
        reply = f"Complaint {complaint_id} is currently {complaint.status}."
        return AgentResponse(
            agent_name="complaint_agent",
            intent=IntentType.COMPLAINT,
            reply=reply,
            confidence=1.0,
            tool_calls=["get_complaint_status"],
        )
