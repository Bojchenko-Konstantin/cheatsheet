from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.interfaces import ICheatsheetRepo, IUnitOfWork
from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.repositories import SQLAlchemyCheatsheetRepo


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = DEFAULT_SESSION_FACTORY,
    ):
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session: AsyncSession = self._session_factory()
        self.cheatsheet_repo: ICheatsheetRepo = SQLAlchemyCheatsheetRepo(self._session)
        return await super().__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await super().__aexit__(*args)
        await self._session.close()

    async def _commit(self) -> None:
        await self._session.commit()

    async def _rollback(self) -> None:
        await self._session.rollback()
