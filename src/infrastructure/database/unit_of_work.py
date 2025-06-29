from typing import TYPE_CHECKING

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
        self._cheatsheet: ICheatsheetRepo = SQLAlchemyCheatsheetRepository(
            session
        )

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
