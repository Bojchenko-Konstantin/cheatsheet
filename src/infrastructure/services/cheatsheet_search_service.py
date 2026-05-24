from src.application.dto.cheatsheet import PaginationMetadata
from src.application.exceptions import (
    InvalidCursorError,
    InvalidSearchQueryError,
    InvalidSortFieldError,
    InvalidSortOrderError,
)
from src.application.interfaces.services import CursorDTO, ICheatsheetSearchService
from src.infrastructure.services.cursor_service import CursorService


class CheatsheetSearchService(ICheatsheetSearchService):
    """Service for cheatsheet search, filtering, and pagination logic."""

    _MIN_SEARCH_LENGTH: int = 2
    _MAX_SUGGESTIONS: int = 10
    _SIMILARITY_THRESHOLD_SEARCH: float = 0.2
    _SIMILARITY_THRESHOLD_SUGGESTIONS: float = 0.2
    _ALLOWED_SORT_FIELDS: frozenset[str] = frozenset(
        {"created_at", "updated_at", "title"}
    )
    _ALLOWED_SORT_ORDERS: frozenset[str] = frozenset({"asc", "desc"})

    def __init__(self, cursor_service: CursorService) -> None:
        """Initialize search service with required cursor service."""
        self._cursor_service = cursor_service

    @property
    def similarity_search_threshold(self) -> float:
        return self._SIMILARITY_THRESHOLD_SEARCH

    @property
    def similarity_suggestions_threshold(self) -> float:
        return self._SIMILARITY_THRESHOLD_SUGGESTIONS

    def validate_search_query(self, query: str | None) -> None:
        if query is not None and len(query.strip()) < self._MIN_SEARCH_LENGTH:
            raise InvalidSearchQueryError

    def validate_sort_params(self, sort_by: str, sort_order: str) -> None:
        if sort_by not in self._ALLOWED_SORT_FIELDS:
            raise InvalidSortFieldError
        if sort_order not in self._ALLOWED_SORT_ORDERS:
            raise InvalidSortOrderError

    def decode_cursor(self, cursor_str: str | None) -> CursorDTO | None:
        """Decode cursor string to CursorDTO with validation."""
        if cursor_str is None:
            return None

        try:
            cursor = self._cursor_service.decode(cursor_str)
            return CursorDTO(
                entity_id=cursor.entity_id,
                sort_value=cursor.sort_value,
            )
        except InvalidCursorError:
            raise
        except Exception as e:
            raise InvalidCursorError from e

    def build_pagination_metadata(
        self,
        rows: list,
        size: int,
        current_cursor: str | None,
        sort_by: str,
    ) -> PaginationMetadata:
        """Build pagination metadata from query results."""
        try:
            has_next = len(rows) > size
            has_previous = current_cursor is not None
            items = rows[:size]

            next_cursor = self._build_next_cursor(items, has_next, sort_by)
            previous_cursor = self._build_previous_cursor(items, has_previous, sort_by)

            return PaginationMetadata(
                next_cursor=next_cursor,
                previous_cursor=previous_cursor,
                has_next=has_next,
                has_previous=has_previous,
            )
        except (KeyError, AttributeError, TypeError) as e:
            raise InvalidCursorError from e

    def validate_suggestions_limit(self, limit: int) -> None:
        if limit > self._MAX_SUGGESTIONS:
            raise InvalidSearchQueryError

    def _build_next_cursor(
        self, items: list, has_next: bool, sort_by: str
    ) -> str | None:
        if not has_next or not items:
            return None
        last_item = items[-1]
        return self._encode_cursor_from_row(last_item, sort_by)

    def _build_previous_cursor(
        self, items: list, has_previous: bool, sort_by: str
    ) -> str | None:
        if not has_previous or not items:
            return None
        first_item = items[0]
        return self._encode_cursor_from_row(first_item, sort_by)

    def _encode_cursor_from_row(self, row, sort_by: str) -> str:
        """Encode cursor from a result row."""
        try:
            cheatsheet_data = row.cheatsheet
            entity_id = cheatsheet_data["cheatsheet_id"]
            sort_value = cheatsheet_data[sort_by]
        except (KeyError, AttributeError, TypeError) as e:
            raise InvalidCursorError from e

        try:
            return self._cursor_service.encode(entity_id, sort_value)
        except Exception as e:
            raise InvalidCursorError from e
