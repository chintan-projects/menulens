"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import Settings, get_settings


def create_engine(settings: Settings | None = None) -> tuple[
    "sqlalchemy.ext.asyncio.AsyncEngine",  # noqa: F821
    async_sessionmaker[AsyncSession],
]:
    """Create async SQLAlchemy engine and session factory.

    Args:
        settings: Application settings. Uses defaults if not provided.

    Returns:
        Tuple of (engine, session_factory).
    """
    if settings is None:
        settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
    )

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return engine, session_factory


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Args:
        session_factory: The session factory to create sessions from.

    Yields:
        An async database session that auto-closes on exit.
    """
    async with session_factory() as session:
        yield session
