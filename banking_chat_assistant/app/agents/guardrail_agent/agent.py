"""Guardrail agent: treats user messages, retrieved documents, and tool outputs as
untrusted input. Screens for prompt-injection patterns and blocks unsafe content."""
import re

from app.core.exceptions import GuardrailViolationError

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+|previous\s+|prior\s+|the\s+|your\s+)*instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+|previous\s+|your\s+|the\s+)*(?:system\s+)?(?:prompt|instructions)", re.IGNORECASE),
    re.compile(r"you are now (in )?(developer|dan|jailbreak) mode", re.IGNORECASE),
    re.compile(r"reveal (your|the) (system )?prompt", re.IGNORECASE),
    re.compile(r"act as (an?|the) unrestricted", re.IGNORECASE),
]


class GuardrailAgent:
    """Runs before orchestration (input screening) and after generation (output screening)."""

    def screen_input(self, message: str) -> None:
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(message):
                raise GuardrailViolationError(
                    "Potential prompt injection detected in user message",
                    {"pattern": pattern.pattern},
                )

    def screen_untrusted_text(self, text: str) -> str:
        """Sanitizes text originating from retrieved documents or tool outputs before
        it is inserted into a prompt, neutralizing any embedded instructions."""
        sanitized = text
        for pattern in _INJECTION_PATTERNS:
            sanitized = pattern.sub("[REDACTED_INSTRUCTION]", sanitized)
        return sanitized
