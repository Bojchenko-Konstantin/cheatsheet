from abc import ABC, abstractmethod

from domain.entities import Cheatsheet


class ICheatsheetRepo(ABC):
    @abstractmethod
    async def get_by_id(self, cheatsheet_id: int) -> Cheatsheet | None:
        pass

    @abstractmethod
    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        pass
