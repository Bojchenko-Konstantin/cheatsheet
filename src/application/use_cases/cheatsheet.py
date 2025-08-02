from abc import ABC, abstractmethod
from dataclasses import asdict

from domain.unit_of_work import UnitOfWork
from src.application.dto.schemas import CheatsheetRead


class ICheatsheetUseCase(ABC):

    @abstractmethod
    async def get_cheatsheet_by_id(self, cheatsheet_id: int) -> CheatsheetRead | None:
        pass


class CheatsheetUseCase(ICheatsheetUseCase):
    def __init__(self, unit_of_work: UnitOfWork):
        self._repo = unit_of_work.cheatsheet_repo

    async def get_cheatsheet_by_id(self, cheatsheet_id: int) -> CheatsheetRead | None:
        cheatsheet = await self._repo.get_by_id(cheatsheet_id)
        if not cheatsheet:
            return None

        return CheatsheetRead(**asdict(cheatsheet))
