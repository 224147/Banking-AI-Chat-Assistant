"""Persists audit events directly (DB write) and publishes them onto the event bus
for downstream compliance/traceability consumers."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.events.producer import EventProducer
from app.schemas.events import EventType


class AuditService:
    def __init__(self, session: AsyncSession, producer: EventProducer) -> None:
        self._session = session
        self._producer = producer

    async def record(
        self,
        event_type: EventType,
        request_id: str,
        *,
        session_id: str | None = None,
        customer_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        payload = payload or {}
        self._session.add(
            AuditLog(
                request_id=request_id,
                session_id=session_id,
                customer_id=customer_id,
                event_type=event_type.value,
                payload=payload,
            )
        )
        await self._session.commit()
        await self._producer.publish(
            EventType.AUDIT_LOGGED,
            request_id,
            session_id=session_id,
            customer_id=customer_id,
            payload={"original_event": event_type.value, **payload},
        )
