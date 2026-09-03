"""Async SQLAlchemy engine/session factory management, keyed by settings."""
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base


@lru_cache
def _get_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True, future=True)


def get_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    engine = _get_engine(settings.database_url)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_models(settings: Settings) -> None:
    """Create tables if they don't exist. For production use Alembic migrations instead."""
    engine = _get_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
