"""Event schemas for the event-driven architecture (RabbitMQ)."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    CHAT_MESSAGE_RECEIVED = "chat.message.received"
    INTENT_CLASSIFIED = "intent.classified"
    AGENT_SELECTED = "agent.selected"
    AGENT_EXECUTED = "agent.executed"
    RAG_DOCUMENTS_RETRIEVED = "rag.documents.retrieved"
    TOOL_EXECUTED = "tool.executed"
    COMPLAINT_CREATED = "complaint.created"
    CARD_BLOCKED = "card.blocked"
    CARD_UNBLOCKED = "card.unblocked"
    RESPONSE_GENERATED = "response.generated"
    AUDIT_LOGGED = "audit.logged"
    NOTIFICATION_GENERATED = "notification.generated"


class BaseEvent(BaseModel):
    event_type: EventType
    request_id: str
    session_id: str | None = None
    customer_id: str | None = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
