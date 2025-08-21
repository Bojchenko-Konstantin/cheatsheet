from abc import ABC, abstractmethod
from typing import Any, Self

from src.domain.repositories import ICheatsheetRepo


class IUnitOfWork(ABC):
    cheatsheet_repo: ICheatsheetRepo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
