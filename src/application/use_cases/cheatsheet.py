from uuid import UUID

from src.application.interfaces import IUnitOfWork
from src.domain.entities import Cheatsheet


class CheatsheetUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._unit_of_work = unit_of_work

    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.get_by_id(cheatsheet_id)
            return cheatsheet

    async def create(self, cheatsheet_to_create: Cheatsheet) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.create(cheatsheet_to_create)
            return cheatsheet

    async def update(self, cheatsheet_with_updated_data: Cheatsheet) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.update(cheatsheet_with_updated_data)
            return cheatsheet
