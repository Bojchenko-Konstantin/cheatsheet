from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CheatsheetBase(BaseModel):
    cheatsheet_id: int
    tag: str
    title: str
    content: str
    author_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    update_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class CheatsheetCreate(CheatsheetBase):
    pass


class CheatsheetUpdate(CheatsheetCreate):
    pass


class CheatsheetUpdatePartial(CheatsheetCreate):
    cheatsheet_id: int | None = None
    tag: str | None = None
    title: str | None = None
    content: str | None = None
    author_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    update_at: datetime | None = None


class TagBase(BaseModel):
    tag_name: str
