from src.application.interfaces import IUnitOfWork
from src.domain.entities import Cheatsheet


class CheatsheetUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._repo = unit_of_work.cheatsheet_repo

    async def get_by_id(self, cheatsheet_id: int) -> Cheatsheet | None:
        cheatsheet = await self._repo.get_by_id(cheatsheet_id)
        if not cheatsheet:
            return None

        return cheatsheet
