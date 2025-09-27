import uuid

from src.application.interfaces import IUnitOfWork
from src.domain.entities import Cheatsheet


class CheatsheetUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._unit_of_work = unit_of_work

    async def get_by_id(self, cheatsheet_id: uuid.UUID) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.get_by_id(cheatsheet_id)
            return cheatsheet
