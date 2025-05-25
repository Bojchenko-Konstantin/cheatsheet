from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CheatsheetBase(BaseModel):
    cheatsheet_id: int
    tag: str
    title: str
    content: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class CheatsheetCreate(BaseModel):
    tag: str
    title: str
    content: str
    user_id: UUID


class CheatsheetUpdate(BaseModel):
    cheatsheet_id: int
    tag: str | None = None
    title: str | None = None
    content: str | None
    user_id: UUID


class CheatsheetUpdatePartial(BaseModel):
    cheatsheet_id: int
    tag: str | None = None
    title: str | None = None
    content: str | None = None
    user_id: UUID


class TagBase(BaseModel):
    tag_name: str
