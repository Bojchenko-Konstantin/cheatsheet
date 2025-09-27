from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class Tag:
    tag_id: int
    tag_name: str


@dataclass(slots=True)
class Cheatsheet:
    cheatsheet_id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    tags: set[Tag]
    count_like: int
    count_view: int

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
