"""Audit and notification consumers. Started as background tasks during app startup."""
from app.clients.broker_client import BrokerClient
from app.core.config import Settings
from app.core.logging import get_logger
from app.db.models import AuditLog
from app.db.session import get_session_factory

logger = get_logger(__name__)


async def audit_consumer_handler(settings: Settings):
    session_factory = get_session_factory(settings)

    async def handler(message: dict) -> None:
        async with session_factory() as session:
            session.add(
                AuditLog(
                    request_id=message.get("request_id", ""),
                    session_id=message.get("session_id"),
                    customer_id=message.get("customer_id"),
                    event_type=message.get("event_type", "unknown"),
                    payload=message.get("payload", {}),
                )
            )
            await session.commit()
        logger.info("audit_event_persisted", event_type=message.get("event_type"))

    return handler


async def notification_consumer_handler():
    async def handler(message: dict) -> None:
        logger.info(
            "notification_dispatched",
            event_type=message.get("event_type"),
            customer_id=message.get("customer_id"),
        )

    return handler


async def start_consumers(broker_client: BrokerClient, settings: Settings) -> None:
    if not broker_client.enabled:
        logger.warning("consumers_not_started_broker_disabled")
        return

    audit_handler = await audit_consumer_handler(settings)
    await broker_client.consume(routing_key="audit.logged", queue_name="audit_queue", handler=audit_handler)

    notification_handler = await notification_consumer_handler()
    for routing_key in ("complaint.created", "card.blocked", "card.unblocked"):
        await broker_client.consume(
            routing_key=routing_key, queue_name="notification_queue", handler=notification_handler
        )
