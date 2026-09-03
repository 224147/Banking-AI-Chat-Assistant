import pytest


@pytest.mark.asyncio
async def test_create_and_fetch_complaint(client):
    response = await client.post(
        "/api/v1/complaints",
        json={"category": "CARD", "description": "My card statement shows an incorrect fee."},
        headers={"Idempotency-Key": "complaint-key-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["escalated"] is False

    fetched = await client.get(f"/api/v1/complaints/{body['complaint_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["complaint_id"] == body["complaint_id"]


@pytest.mark.asyncio
async def test_complaint_escalation_keyword(client):
    response = await client.post(
        "/api/v1/complaints",
        json={"category": "CARD", "description": "This is an unauthorized fraud transaction, please help urgently."},
        headers={"Idempotency-Key": "complaint-key-2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["escalated"] is True
    assert body["status"] == "ESCALATED"


@pytest.mark.asyncio
async def test_get_nonexistent_complaint_returns_404(client):
    response = await client.get("/api/v1/complaints/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error_code"] == "RESOURCE_NOT_FOUND"
