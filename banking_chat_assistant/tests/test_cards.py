import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import Card
from app.db.seed import DEMO_CUSTOMER_ID
from app.db.session import get_session_factory


@pytest.mark.asyncio
async def test_card_block_and_unblock_with_idempotency(client):
    session_factory = get_session_factory(get_settings())
    async with session_factory() as session:
        result = await session.execute(select(Card).where(Card.customer_id == DEMO_CUSTOMER_ID))
        card = result.scalars().first()
    card_id = card.card_id

    response = await client.post(
        "/api/v1/cards/block",
        json={"card_id": card_id, "card_type": card.card_type},
        headers={"Idempotency-Key": "block-key-1"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"

    # Same idempotency key returns the cached response without re-executing.
    repeat = await client.post(
        "/api/v1/cards/block",
        json={"card_id": card_id, "card_type": card.card_type},
        headers={"Idempotency-Key": "block-key-1"},
    )
    assert repeat.status_code == 200
    assert repeat.json() == response.json()

    unblock = await client.post(
        "/api/v1/cards/unblock",
        json={"card_id": card_id, "card_type": card.card_type},
        headers={"Idempotency-Key": "unblock-key-1"},
    )
    assert unblock.status_code == 200
    assert unblock.json()["status"] == "ACTIVE"
