from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.application.dto import CheatsheetList, CheatsheetSearchSuggestions
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

    @abstractmethod
    async def list_accessible_cheatsheets(
        self,
        user_id: UUID | None,
        cursor: str | None,
        size: int,
        tag: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
    ) -> CheatsheetList:
        pass

    @abstractmethod
    async def search_suggestions(
        self,
        query: str,
        limit: int,
    ) -> CheatsheetSearchSuggestions:
        pass
