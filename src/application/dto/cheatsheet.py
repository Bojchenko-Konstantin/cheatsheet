from dataclasses import dataclass

from src.domain.entities import Cheatsheet


@dataclass(slots=True, frozen=True)
class CheatsheetList:
    """DTO for paginated cheatsheet list response."""

    items: list[Cheatsheet]
    next_cursor: str | None
    previous_cursor: str | None
    has_next: bool
    has_previous: bool


@dataclass(slots=True, frozen=True)
class CheatsheetSearchSuggestions:
    """DTO for search autocomplete suggestions."""

    titles: list[str]
    tags: list[str]


@dataclass(slots=True, frozen=True)
class PaginationMetadata:
    """Metadata for cursor-based pagination.

    Contains computed pagination state derived from query results
    to inform clients about available navigation options.
    """

    next_cursor: str | None
    previous_cursor: str | None
    has_next: bool
    has_previous: bool
