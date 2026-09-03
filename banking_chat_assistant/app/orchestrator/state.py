"""Shared orchestration state passed between LangGraph nodes."""
from typing import TypedDict

from app.schemas.chat import AgentContext, AgentResponse, IntentType


class OrchestratorState(TypedDict, total=False):
    context: AgentContext
    intent: IntentType
    response: AgentResponse
    error: str | None
