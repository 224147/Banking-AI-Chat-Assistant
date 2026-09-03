import pytest


@pytest.mark.asyncio
async def test_get_balance(client):
    response = await client.post("/api/v1/account/balance", json={"account_id": "unused"})
    assert response.status_code == 200
    body = response.json()
    assert body["available_balance"] > 0
    assert body["account_number_masked"].startswith("*")


@pytest.mark.asyncio
async def test_get_transactions(client):
    response = await client.post("/api/v1/account/transactions", json={"account_id": "unused", "limit": 5})
    assert response.status_code == 200
    assert len(response.json()["transactions"]) > 0
