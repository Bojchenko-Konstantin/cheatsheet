from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.interfaces import ICheatsheetRepo, IJWTRepo, IUnitOfWork, IUserRepo
from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.repositories import (
    SQLAlchemyCheatsheetRepo,
    SQLAlchemyJWTRepo,
    SQLAlchemyUserRepo,
)


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = DEFAULT_SESSION_FACTORY,
        read_only: bool = False,
    ):
        self._session_factory = session_factory
        self._read_only = read_only

    def readonly(self) -> Self:
        return self.__class__(session_factory=self._session_factory, read_only=True)

    async def __aenter__(self) -> Self:
        self._session: AsyncSession = self._session_factory()
        self.cheatsheet_repo: ICheatsheetRepo = SQLAlchemyCheatsheetRepo(self._session)
        self.user_repo: IUserRepo = SQLAlchemyUserRepo(self._session)
        self.jwt_repo: IJWTRepo = SQLAlchemyJWTRepo(self._session)

        if not self._read_only:
            await self._session.begin()

        return await super().__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        if self._read_only:
            await self._session.close()

        else:
            await super().__aexit__(*args)
            await self._session.close()

    async def _commit(self) -> None:
        if not self._read_only and self._session:
            await self._session.commit()

    async def _rollback(self) -> None:
        if not self._read_only and self._session:
            await self._session.rollback()
