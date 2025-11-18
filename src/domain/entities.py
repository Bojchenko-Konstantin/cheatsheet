from collections.abc import Mapping, MutableMapping
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Self
from uuid import UUID


@dataclass(slots=True, frozen=True)
class Tag:
    tag_id: int
    tag_name: str | None = None


@dataclass(slots=True)
class Cheatsheet:
    cheatsheet_id: UUID
    title: str
    content: str
    is_public: bool
    tags: set[Tag]
    created_at: datetime
    updated_at: datetime
    count_like: int = 0
    count_view: int = 0

    @classmethod
    def from_dict(cls, kwargs: MutableMapping) -> Self:
        if not isinstance(kwargs["tags"], set):
            kwargs["tags"] = {Tag(**tag) for tag in kwargs["tags"]}
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return asdict(self)

    def update(self, kwargs: Mapping) -> Self:
        for key, value in kwargs.items():
            if key == "tags" and not isinstance(value, set):
                value = {Tag(**tag) for tag in value}
            setattr(self, key, value)
        return self

    def add_tag(self, new_tag: Tag) -> None:
        self.tags.add(new_tag)

    def remove_tag(self, tag: Tag) -> None:
        self.tags.discard(tag)

    def increase_like_count(self) -> None:
        self.count_like += 1

    def decrease_like_count(self) -> None:
        self.count_like -= 1

    def increase_view_count(self) -> None:
        self.count_view += 1

    def set_public(self) -> None:
        self.is_public = True

    def set_private(self) -> None:
        self.is_public = False
