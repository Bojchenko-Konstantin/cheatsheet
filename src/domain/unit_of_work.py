from abc import ABC, abstractmethod
from typing import Any, Self


class UnitOfWork(ABC):
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
