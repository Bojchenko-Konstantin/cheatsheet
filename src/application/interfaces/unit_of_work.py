from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.application.interfaces import ICheatsheetRepo, IUserRepo


class IUnitOfWork(ABC):
    """
    Abstract class for atomicity, consistency and data integrity
    during operations with data.
    """

    cheatsheet_repo: ICheatsheetRepo
    user_repo: IUserRepo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        The commit and rollback are made automatically on exit from context manager
        for simplicity sake. Also it is possible only due to low system load.
        """
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
