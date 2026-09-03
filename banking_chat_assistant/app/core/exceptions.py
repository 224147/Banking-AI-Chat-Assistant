"""Custom exception hierarchy. Provider-specific errors must never leak to clients."""
from typing import Any


class BankingAssistantError(Exception):
    """Base class for all application errors."""

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentTimeoutError(BankingAssistantError):
    error_code = "AGENT_TIMEOUT"
    status_code = 504


class RetrievalNotFoundError(BankingAssistantError):
    error_code = "RETRIEVAL_NOT_FOUND"
    status_code = 404


class LLMProviderError(BankingAssistantError):
    error_code = "LLM_PROVIDER_ERROR"
    status_code = 502


class BrokerUnavailableError(BankingAssistantError):
    error_code = "BROKER_UNAVAILABLE"
    status_code = 503


class InvalidAgentOutputError(BankingAssistantError):
    error_code = "INVALID_AGENT_OUTPUT"
    status_code = 502


class ToolExecutionError(BankingAssistantError):
    error_code = "TOOL_EXECUTION_ERROR"
    status_code = 502


class ResourceNotFoundError(BankingAssistantError):
    error_code = "RESOURCE_NOT_FOUND"
    status_code = 404


class AuthenticationError(BankingAssistantError):
    error_code = "AUTHENTICATION_ERROR"
    status_code = 401


class IdempotencyConflictError(BankingAssistantError):
    error_code = "IDEMPOTENCY_CONFLICT"
    status_code = 409


class GuardrailViolationError(BankingAssistantError):
    error_code = "GUARDRAIL_VIOLATION"
    status_code = 400
