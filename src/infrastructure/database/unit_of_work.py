from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces import IUnitOfWork
from src.application.interfaces.repositories import ICheatsheetRepo
from src.infrastructure.repositories import SQLAlchemyCheatsheetRepo


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> Self:
        self.cheatsheet_repo: ICheatsheetRepo = SQLAlchemyCheatsheetRepo(self._session)
        return await super().__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        return await super().__aexit__(*args)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
