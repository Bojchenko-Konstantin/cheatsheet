from abc import ABC, abstractmethod
from dataclasses import asdict

from src.application.dto.schemas import CheatsheetRead
from src.domain.unit_of_work import IUnitOfWork


class ICheatsheetUseCase(ABC):
    @abstractmethod
    async def get_by_id(self, cheatsheet_id: int) -> CheatsheetRead | None:
        pass


class CheatsheetUseCase(ICheatsheetUseCase):
    def __init__(self, unit_of_work: IUnitOfWork):
        self._repo = unit_of_work.cheatsheet_repo

    async def get_by_id(self, cheatsheet_id: int) -> CheatsheetRead | None:
        cheatsheet = await self._repo.get_by_id(cheatsheet_id)
        if not cheatsheet:
            return None

        return CheatsheetRead(**asdict(cheatsheet))
