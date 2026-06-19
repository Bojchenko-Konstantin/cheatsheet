from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.interfaces import IUnitOfWork
from src.application.interfaces.services import ICheatsheetSearchService
from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.repositories import (
    SQLAlchemyCheatsheetRepo,
    SQLAlchemyOAuthRepo,
    SQLAlchemyTokenRepo,
    SQLAlchemyUserRepo,
)


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = DEFAULT_SESSION_FACTORY,
        search_service: ICheatsheetSearchService | None = None,
        read_only: bool = False,
    ):
        self._session_factory = session_factory
        self._search_service = search_service
        self._read_only = read_only
        self._session: AsyncSession | None = None

    def readonly(self) -> Self:
        return self.__class__(
            session_factory=self._session_factory,
            search_service=self._search_service,
            read_only=True,
        )

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()

        self.cheatsheet_repo = SQLAlchemyCheatsheetRepo(
            self._session,
            search_service=self._search_service,  # type: ignore[arg-type]
        )
        self.user_repo = SQLAlchemyUserRepo(self._session)
        self.token_repo = SQLAlchemyTokenRepo(self._session)
        self.oauth_repo = SQLAlchemyOAuthRepo(self._session)

        if not self._read_only:
            await self._session.begin()

        return await super().__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        if self._read_only:
            if self._session:
                await self._session.close()
        else:
            await super().__aexit__(*args)
            if self._session:
                await self._session.close()

    async def _commit(self) -> None:
        if not self._read_only and self._session:
            await self._session.commit()

    async def _rollback(self) -> None:
        if not self._read_only and self._session:
            await self._session.rollback()
