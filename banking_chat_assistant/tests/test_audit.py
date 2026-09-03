"""Verifies chat requests produce a persisted audit trail and the documented events."""
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import AuditLog
from app.db.session import get_session_factory


@pytest.mark.asyncio
async def test_chat_writes_audit_log(client):
    response = await client.post(
        "/api/v1/chat", json={"session_id": "audit-session", "message": "What is my account balance?"}
    )
    assert response.status_code == 200
    request_id = response.json()["request_id"]

    session_factory = get_session_factory(get_settings())
    async with session_factory() as session:
        result = await session.execute(select(AuditLog).where(AuditLog.request_id == request_id))
        logs = result.scalars().all()

    assert len(logs) == 1
    assert logs[0].session_id == "audit-session"
    assert logs[0].payload["intent"] == "BALANCE_INQUIRY"
    # Raw prompts must never be persisted in the audit trail.
    assert "message" not in logs[0].payload
