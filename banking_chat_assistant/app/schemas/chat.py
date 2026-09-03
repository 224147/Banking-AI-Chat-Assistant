"""Chat / conversation / agent request-response Pydantic v2 models."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    BALANCE_INQUIRY = "BALANCE_INQUIRY"
    TRANSACTION_HISTORY = "TRANSACTION_HISTORY"
    CARD_SERVICES = "CARD_SERVICES"
    LOAN_INFORMATION = "LOAN_INFORMATION"
    FAQ = "FAQ"
    COMPLAINT = "COMPLAINT"
    OTHER = "OTHER"


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client conversation/session identifier")
    message: str = Field(..., min_length=1, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceCitation(BaseModel):
    document_id: str
    title: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    intent: IntentType
    reply: str
    citations: list[SourceCitation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    agent_name: str
    request_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentContext(BaseModel):
    session_id: str
    customer_id: str
    request_id: str
    message: str
    conversation_history: list[dict[str, str]] = Field(default_factory=list)


class RetrievalContext(BaseModel):
    query: str
    documents: list[SourceCitation] = Field(default_factory=list)
    average_confidence: float = 0.0


class ConversationState(BaseModel):
    session_id: str
    turns: list[dict[str, str]] = Field(default_factory=list)
    token_count: int = 0
    summary: str | None = None


class AgentResponse(BaseModel):
    agent_name: str
    intent: IntentType
    reply: str
    citations: list[SourceCitation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    tool_calls: list[str] = Field(default_factory=list)
