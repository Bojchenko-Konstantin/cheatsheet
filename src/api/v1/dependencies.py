from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.cheatsheet import CheatsheetUseCase
from src.infrastructure.database.database_helper import db_helper
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_helper.session_getter():
        yield session


async def get_unit_of_work(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyUnitOfWork:
    async with SQLAlchemyUnitOfWork(session) as unit_of_work:
        return unit_of_work


async def get_cheatsheet_use_case(
    unit_of_work: SQLAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(unit_of_work=unit_of_work)
