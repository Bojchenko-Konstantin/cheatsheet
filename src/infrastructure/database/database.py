from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

ENGINE: AsyncEngine = create_async_engine(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)


async def dispose() -> None:
    await ENGINE.dispose()


DEFAULT_SESSION_FACTORY: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=ENGINE,
    autoflush=True,
    autocommit=False,
    expire_on_commit=False,
)
