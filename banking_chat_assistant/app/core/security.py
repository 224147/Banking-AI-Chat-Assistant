"""Lightweight session-token verification. Client-provided identifiers are never trusted directly."""
import hashlib
import hmac
import time

from app.core.config import Settings
from app.core.exceptions import AuthenticationError


def issue_session_token(customer_id: str, settings: Settings, ttl_seconds: int = 3600) -> str:
    expiry = int(time.time()) + ttl_seconds
    payload = f"{customer_id}:{expiry}"
    signature = _sign(payload, settings.session_secret_key)
    return f"{payload}:{signature}"


def verify_session_token(token: str, settings: Settings) -> str:
    """Returns the verified customer_id or raises AuthenticationError."""
    try:
        customer_id, expiry_str, signature = token.split(":")
        expiry = int(expiry_str)
    except (ValueError, AttributeError) as exc:
        raise AuthenticationError("Malformed session token") from exc

    payload = f"{customer_id}:{expiry_str}"
    expected_signature = _sign(payload, settings.session_secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthenticationError("Invalid session token signature")
    if time.time() > expiry:
        raise AuthenticationError("Session token expired")
    return customer_id


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
