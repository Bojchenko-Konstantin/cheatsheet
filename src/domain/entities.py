from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Tag:
    tag_id: int
    tag_name: str


@dataclass(slots=True)
class Cheatsheet:
    cheatsheet_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    tags: set[Tag]
    count_like: int
    count_view: int
