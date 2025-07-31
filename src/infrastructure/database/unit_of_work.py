from typing import TYPE_CHECKING, Any, Self

from domain.repositories.cheatsheet import (
    ICheatsheetRepo,
)
from domain.unit_of_work import UnitOfWork
from infrastructure.repositories.cheatsheet_repository import (
    SQLAlchemyCheatsheetRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> Self:
        self._cheatsheet: ICheatsheetRepo = SQLAlchemyCheatsheetRepository(
            self._session
        )
        return await super().__aenter__()

    async def __aexit__(self, *args: Any):
        return await super().__aexit__(*args)

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
