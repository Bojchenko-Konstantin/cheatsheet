from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Cheatsheet:
    cheatsheet_id: int
    title: str
    content: str
    created_at: datetime
    update_at: datetime
    is_public: bool
    tag_ids: List["Tag"]
    count_like: int
    count_view: int


@dataclass
class Tag:
    tag_id: int
    tag_name: str
