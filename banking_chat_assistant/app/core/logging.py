"""Structured JSON logging configuration with PII masking."""
import logging
import re
import sys
from typing import Any

import structlog

_PII_PATTERNS = [
    (re.compile(r"\b\d{12,19}\b"), "***MASKED_ACCOUNT***"),  # account/card numbers
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "***MASKED_CARD***"),
]


def _mask_pii(_logger: Any, _method_name: str, event_dict: dict) -> dict:
    for key in ("message", "event", "query", "prompt", "raw_prompt"):
        value = event_dict.get(key)
        if isinstance(value, str):
            for pattern, replacement in _PII_PATTERNS:
                value = pattern.sub(replacement, value)
            event_dict[key] = value
    # Never persist raw prompts
    event_dict.pop("raw_prompt", None)
    return event_dict


def configure_logging(debug: bool = False) -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if debug else logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _mask_pii,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)
