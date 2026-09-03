"""Publishes domain events onto RabbitMQ via the BrokerClient."""
from app.clients.broker_client import BrokerClient
from app.schemas.events import BaseEvent, EventType


class EventProducer:
    def __init__(self, broker_client: BrokerClient) -> None:
        self._broker_client = broker_client

    async def publish(
        self,
        event_type: EventType,
        request_id: str,
        *,
        session_id: str | None = None,
        customer_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        event = BaseEvent(
            event_type=event_type,
            request_id=request_id,
            session_id=session_id,
            customer_id=customer_id,
            payload=payload or {},
        )
        await self._broker_client.publish(event)
