"""Idempotency-Key handling for sensitive actions (card block/unblock, complaint creation)."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IdempotencyConflictError
from app.db.models import IdempotencyKey


async def get_cached_response(session: AsyncSession, key: str, customer_id: str) -> dict | None:
    result = await session.execute(
        select(IdempotencyKey).where(IdempotencyKey.key == key, IdempotencyKey.customer_id == customer_id)
    )
    record = result.scalar_one_or_none()
    return record.response_payload if record else None


async def store_response(session: AsyncSession, key: str, customer_id: str, response_payload: dict) -> None:
    session.add(IdempotencyKey(key=key, customer_id=customer_id, response_payload=response_payload))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IdempotencyConflictError("Idempotency key was used concurrently") from exc
