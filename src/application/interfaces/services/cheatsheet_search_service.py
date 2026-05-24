from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.application.dto.cheatsheet import PaginationMetadata


@dataclass(slots=True, frozen=True)
class CursorDTO:
    """DTO for cursor data in application layer."""

    entity_id: UUID
    sort_value: datetime | str | int


class ICheatsheetSearchService(ABC):
    """Interface for cheatsheet search and pagination logic."""

    @property
    @abstractmethod
    def similarity_search_threshold(self) -> float:
        """Get similarity threshold for full-text search queries."""
        pass

    @property
    @abstractmethod
    def similarity_suggestions_threshold(self) -> float:
        """Get similarity threshold for autocomplete suggestions."""
        pass

    @abstractmethod
    def validate_search_query(self, query: str | None) -> None:
        """Validate search query meets minimum length requirements."""
        pass

    @abstractmethod
    def validate_sort_params(self, sort_by: str, sort_order: str) -> None:
        """Validate sorting parameters against allowed values."""
        pass

    @abstractmethod
    def decode_cursor(self, cursor_str: str | None) -> CursorDTO | None:
        """Decode cursor string to CursorDTO with validation."""
        pass

    @abstractmethod
    def build_pagination_metadata(
        self,
        rows: list,
        size: int,
        current_cursor: str | None,
        sort_by: str,
    ) -> PaginationMetadata:
        """Build pagination metadata from query results."""
        pass

    @abstractmethod
    def validate_suggestions_limit(self, limit: int) -> None:
        """Validate suggestions limit is within allowed range."""
        pass
