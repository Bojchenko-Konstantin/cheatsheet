from fastapi import Depends

from src.application.interfaces import IUnitOfWork
from src.application.use_cases import CheatsheetUseCase
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def get_unit_of_work() -> IUnitOfWork:
    async with SQLAlchemyUnitOfWork() as unit_of_work:
        return unit_of_work


async def get_cheatsheet_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(unit_of_work=unit_of_work)
