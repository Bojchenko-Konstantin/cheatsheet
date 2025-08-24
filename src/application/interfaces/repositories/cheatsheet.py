from abc import ABC, abstractmethod

from src.domain.entities import Cheatsheet


class ICheatsheetRepo(ABC):
    @abstractmethod
    async def get_by_id(self, cheatsheet_id: int) -> Cheatsheet:
        pass

    @abstractmethod
    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        pass
