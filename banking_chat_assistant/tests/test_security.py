import pytest

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import issue_session_token, verify_session_token


def test_issue_and_verify_session_token():
    settings = get_settings()
    token = issue_session_token("cust_1", settings)
    assert verify_session_token(token, settings) == "cust_1"


def test_verify_rejects_tampered_token():
    settings = get_settings()
    token = issue_session_token("cust_1", settings)
    tampered = token.replace("cust_1", "cust_2")
    with pytest.raises(AuthenticationError):
        verify_session_token(tampered, settings)


def test_verify_rejects_expired_token():
    settings = get_settings()
    token = issue_session_token("cust_1", settings, ttl_seconds=-1)
    with pytest.raises(AuthenticationError):
        verify_session_token(token, settings)


def test_verify_rejects_malformed_token():
    with pytest.raises(AuthenticationError):
        verify_session_token("not-a-token", get_settings())
