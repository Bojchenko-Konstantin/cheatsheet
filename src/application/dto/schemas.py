from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, Field, StrictBool

type PositiveInt = Annotated[int, Field(ge=0)]
type PositiveListInt = list[PositiveInt]
type TagList = Annotated[PositiveListInt, Field(max_length=6)]
type Title = Annotated[str, Field(min_length=3, max_length=50)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        revalidate_instances="always",
    )


class TagBase(Schema):
    tag_name: Annotated[str, Field(max_length=35)]


class TagCreate(TagBase):
    pass


class TagRead(BaseModel):
    tag_id: int
    tag_name: str


class CheatsheetBase(Schema):
    tag_ids: TagList
    title: Title
    is_public: StrictBool
    content: str


class CheatsheetRead(BaseModel):
    cheatsheet_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    tags: list[TagRead]
    count_like: int
    count_view: int


class CheatsheetCreate(CheatsheetBase):
    pass


class CheatsheetUpdate(CheatsheetBase):
    pass


class CheatsheetUpdatePartial(Schema):
    tag_ids: TagList | None = None
    title: Title | None = None
    is_public: StrictBool | None = None
    content: str | None = None


class UserRead(schemas.BaseUser[UUID]):
    user_id: UUID
    first_name: str
    last_name: str
    login: str
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt
    profile_url: list[str]


class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str
    login: str
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt
    profile_url: list[str]


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
    login: str | None = None
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt | None = None
    profile_url: list[str] | None = None
