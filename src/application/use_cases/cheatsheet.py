from abc import ABC, abstractmethod
from dataclasses import asdict

from src.application.dto.schemas import CheatsheetRead
from src.infrastructure.repositories.cheatsheet_repository import (
    SQLAlchemyCheatsheetRepository,
)


class ICheatsheetUseCase(ABC):

    @abstractmethod
    async def get_cheatsheet_by_id(self, cheatsheet_id: int) -> CheatsheetRead | None:
        pass


class CheatsheetUseCase(ICheatsheetUseCase):
    def __init__(
        self,
        repo: SQLAlchemyCheatsheetRepository,
    ):
        self._repo = repo

    async def get_cheatsheet_by_id(self, cheatsheet_id: int) -> CheatsheetRead | None:
        cheatsheet = await self._repo.get_by_id(cheatsheet_id)
        if not cheatsheet:
            return None

        return CheatsheetRead(**asdict(cheatsheet))
