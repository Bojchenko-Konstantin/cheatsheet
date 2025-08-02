from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.cheatsheet import (
    ICheatsheetRepo,
)
from src.domain.unit_of_work import UnitOfWork
from src.infrastructure.repositories.cheatsheet_repository import (
    SQLAlchemyCheatsheetRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> Self:
        self.cheatsheet_repo: ICheatsheetRepo = SQLAlchemyCheatsheetRepository(
            self._session
        )
        return await super().__aenter__()

    async def __aexit__(self, *args: Any):
        return await super().__aexit__(*args)

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
