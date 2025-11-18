from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.domain.entities import Cheatsheet


class ICheatsheetRepo(ABC):
    """Abstract class for operations with cheatsheet storage."""

    @abstractmethod
    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        pass

    @abstractmethod
    async def create(self, create_data: dict[str, Any]) -> Cheatsheet:
        pass

    @abstractmethod
    async def update(self, update_data: dict[str, Any]) -> Cheatsheet:
        pass
