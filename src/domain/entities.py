from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Self
from uuid import UUID

from src.domain.exceptions import (
    CheatsheetAccessDeniedError,
    CheatsheetModificationDeniedError,
    InvalidCheatsheetContentError,
    InvalidCheatsheetTitleError,
    InvalidTagError,
    NegativeStatsError,
    TagLimitExceededError,
)

MAX_TAGS_PER_CHEATSHEET: int = 6
MAX_TITLE_LENGTH: int = 50
MIN_TITLE_LENGTH: int = 3


@dataclass(slots=True, frozen=True)
class Tag:
    tag_id: int
    tag_name: str | None = None

    def __post_init__(self) -> None:
        if self.tag_id <= 0:
            raise InvalidTagError

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return NotImplemented
        return self.tag_id == other.tag_id

    def __hash__(self) -> int:
        return hash(self.tag_id)


@dataclass(slots=True, frozen=True)
class CheatsheetStats:
    count_like: int = 0
    count_view: int = 0

    def __post_init__(self) -> None:
        if self.count_like < 0:
            raise NegativeStatsError
        if self.count_view < 0:
            raise NegativeStatsError

    def add_like(self) -> "CheatsheetStats":
        """Return new stats with incremented like count."""
        return CheatsheetStats(
            count_like=self.count_like + 1,
            count_view=self.count_view,
        )

    def remove_like(self) -> "CheatsheetStats":
        """Return new stats with decremented like count."""
        if self.count_like == 0:
            raise NegativeStatsError
        return CheatsheetStats(
            count_like=self.count_like - 1,
            count_view=self.count_view,
        )

    def add_view(self) -> "CheatsheetStats":
        """Return new stats with incremented view count."""
        return CheatsheetStats(
            count_like=self.count_like,
            count_view=self.count_view + 1,
        )


@dataclass(slots=True)
class Cheatsheet:
    cheatsheet_id: UUID
    user_id: UUID
    title: str
    content: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    tags: set[Tag] = field(default_factory=set)
    stats: CheatsheetStats = field(default_factory=CheatsheetStats)

    def __post_init__(self) -> None:
        """Validate all invariants after construction."""
        self._validate_title(self.title)
        self._validate_content(self.content)
        self._validate_tag_count(self.tags)

    @classmethod
    def from_dict(cls, kwargs: Mapping) -> Self:
        data = dict(kwargs)

        if "tags" in data and not isinstance(data["tags"], set):
            data["tags"] = {Tag(**tag) for tag in data["tags"]}

        if isinstance(data.get("user_id"), str):
            data["user_id"] = UUID(data["user_id"])

        count_like = data.pop("count_like", 0)
        count_view = data.pop("count_view", 0)
        data["stats"] = CheatsheetStats(count_like=count_like, count_view=count_view)

        return cls(**data)

    def to_dict(self) -> dict:
        return asdict(self)

    def is_accessible_by(self, user_id: UUID | None) -> bool:
        """Check whether a user can view this cheatsheet."""
        return self.is_public or (user_id is not None and self.user_id == user_id)

    def is_owned_by(self, user_id: UUID) -> bool:
        """Check whether the given user is the owner."""
        return self.user_id == user_id

    def ensure_accessible_by(self, user_id: UUID | None) -> None:
        """Raise an error if the user cannot view this cheatsheet."""
        if not self.is_accessible_by(user_id):
            raise CheatsheetAccessDeniedError

    def ensure_owned_by(self, user_id: UUID) -> None:
        """Raise an error if the user does not own this cheatsheet."""
        if not self.is_owned_by(user_id):
            raise CheatsheetModificationDeniedError

    def update(
        self,
        *,
        title: str | None = None,
        content: str | None = None,
        is_public: bool | None = None,
        tags: set[Tag] | None = None,
    ) -> Self:
        """Update mutable fields with validation."""
        if title is not None:
            self._validate_title(title)
            self.title = title

        if content is not None:
            self._validate_content(content)
            self.content = content

        if is_public is not None:
            self.is_public = is_public

        if tags is not None:
            self._validate_tag_count(tags)
            self.tags = tags

        return self

    @staticmethod
    def _validate_title(title: str) -> None:
        stripped = title.strip()
        if len(stripped) < MIN_TITLE_LENGTH:
            raise InvalidCheatsheetTitleError
        if len(stripped) > MAX_TITLE_LENGTH:
            raise InvalidCheatsheetTitleError

    @staticmethod
    def _validate_content(content: str) -> None:
        if not content or not content.strip():
            raise InvalidCheatsheetContentError

    @staticmethod
    def _validate_tag_count(tags: set[Tag]) -> None:
        if len(tags) > MAX_TAGS_PER_CHEATSHEET:
            raise TagLimitExceededError
