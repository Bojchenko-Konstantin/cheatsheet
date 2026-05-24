import contextlib
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.application.exceptions import InvalidCursorError


@dataclass(slots=True, frozen=True)
class Cursor:
    """Decoded cursor data for pagination."""

    entity_id: UUID
    sort_value: datetime | str | int


class CursorService:
    """Service for encoding and decoding cursor pagination tokens."""

    @staticmethod
    def encode(entity_id: UUID, sort_value: datetime | str | int) -> str:
        """Encode entity ID and sort value into an opaque cursor string."""
        clean_id = str(entity_id).replace("-", "")

        if isinstance(sort_value, datetime):
            sort_str = str(int(sort_value.timestamp()))
        else:
            sort_str = str(sort_value)

        return f"{clean_id}_{sort_str}"

    @staticmethod
    def decode(cursor: str) -> Cursor:
        """Decode cursor string back to structured cursor data."""
        try:
            id_hex, sort_value = cursor.split("_", 1)
            entity_id = UUID(hex=id_hex)
        except (ValueError, AttributeError) as e:
            raise InvalidCursorError from e

        with contextlib.suppress(ValueError, OSError, TypeError):
            sort_value = datetime.fromtimestamp(int(sort_value))

        return Cursor(entity_id=entity_id, sort_value=sort_value)
