import pytest


@pytest.mark.asyncio
async def test_liveness(client):
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness(client):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
