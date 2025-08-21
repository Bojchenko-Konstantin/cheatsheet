from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.application.interfaces import ICheatsheetRepo


class IUnitOfWork(ABC):
    cheatsheet_repo: ICheatsheetRepo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            await self._commit()
        else:
            await self._rollback()

    @abstractmethod
    async def _commit(self) -> None:
        pass

    @abstractmethod
    async def _rollback(self) -> None:
        pass
