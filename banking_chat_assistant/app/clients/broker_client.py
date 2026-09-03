"""RabbitMQ broker client (aio-pika). Degrades gracefully (logs + no-ops) if the
broker cannot be reached, so the API stays available even if RabbitMQ is down."""
from __future__ import annotations

import json
from typing import ClassVar

import aio_pika
from aio_pika import ExchangeType
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.events import BaseEvent

logger = get_logger(__name__)


class BrokerClient:
    _instance: ClassVar["BrokerClient | None"] = None

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None
        self._exchange: aio_pika.Exchange | None = None
        self.enabled = False

    @classmethod
    def get_instance(cls, settings: Settings) -> "BrokerClient":
        if cls._instance is None:
            cls._instance = cls(settings)
        return cls._instance

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8), reraise=False)
    async def connect(self) -> None:
        try:
            self._connection = await aio_pika.connect_robust(self._settings.rabbitmq_url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self._settings.rabbitmq_exchange, ExchangeType.TOPIC, durable=True
            )
            self.enabled = True
            logger.info("broker_connected", exchange=self._settings.rabbitmq_exchange)
        except Exception as exc:
            self.enabled = False
            logger.warning("broker_connection_failed", error=str(exc))

    async def publish(self, event: BaseEvent) -> None:
        if not self.enabled or self._exchange is None:
            logger.warning("broker_publish_skipped_degraded_mode", event_type=event.event_type.value)
            return
        message = aio_pika.Message(body=event.model_dump_json().encode(), content_type="application/json")
        await self._exchange.publish(message, routing_key=event.event_type.value)

    async def consume(self, routing_key: str, queue_name: str, handler) -> None:
        if not self.enabled or self._channel is None or self._exchange is None:
            logger.warning("broker_consume_skipped_degraded_mode", routing_key=routing_key)
            return
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(self._exchange, routing_key=routing_key)

        async def _on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                await handler(json.loads(message.body))

        await queue.consume(_on_message)

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
