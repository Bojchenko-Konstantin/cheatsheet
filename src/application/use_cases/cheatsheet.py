from abc import ABC, abstractmethod

from application.dto.schemas import (
    CheatsheetRead,
)
from domain.unit_of_work import UnitOfWork
from infrastructure.repositories.cheatsheet_repository import (
    SQLAlchemyCheatsheetRepository,
)


class ICheatsheetUseCase(ABC):

    @abstractmethod
    async def get_cheatsheet_by_id(
        self, cheatsheet_id: int
    ) -> CheatsheetRead | None:
        pass


class CheatsheetUseCase(ICheatsheetUseCase):
    def __init__(
        self,
        repo: SQLAlchemyCheatsheetRepository,
        uow: UnitOfWork,
    ):
        self._repo = repo
        self._uow = uow

    async def get_cheatsheet_by_id(
        self, cheatsheet_id: int
    ) -> CheatsheetRead | None:
        cheatsheet = await self._repo.get_by_id(cheatsheet_id)
        return (
            CheatsheetRead.model_validate(cheatsheet) if cheatsheet else None
        )
