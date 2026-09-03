"""Shared error response schema."""
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error_code: str = Field(..., examples=["AGENT_TIMEOUT"])
    message: str = Field(..., examples=["Agent execution timeout."])
    details: dict[str, Any] = Field(default_factory=dict)
