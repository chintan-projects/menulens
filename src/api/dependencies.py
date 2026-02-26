"""FastAPI dependency injection for database sessions and services."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config.settings import Settings, get_settings
from src.db.engine import create_engine

_engine_and_factory: tuple[object, async_sessionmaker[AsyncSession]] | None = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory singleton.

    Returns:
        Async session factory.
    """
    global _engine_and_factory  # noqa: PLW0603
    if _engine_and_factory is None:
        _engine, factory = create_engine()
        _engine_and_factory = (_engine, factory)
    return _engine_and_factory[1]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for request handling.

    Yields:
        Database session that auto-closes after the request.
    """
    factory = _get_session_factory()
    async with factory() as session:
        yield session


# Type aliases for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]
