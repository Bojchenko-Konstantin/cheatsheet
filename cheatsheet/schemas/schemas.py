from typing import Annotated
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, Field

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


class CheatsheetCreate(Schema):
    tag_id: TagList
    title: Title
    is_public: bool
    content: str


class CheatsheetUpdate(Schema):
    tag_id: TagList
    title: Title
    is_public: bool
    content: str


class CheatsheetUpdatePartial(Schema):
    tag_ids: TagList | None = None
    title: Title | None = None
    is_public: bool | None = None
    content: str | None = None


class CreateTag(Schema):
    tag_name: Annotated[str, Field(max_length=35)]


class UserRead(schemas.BaseUser[UUID]):
    first_name: str
    last_name: str
    login: str
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt
    profile_url: str | list[str]


class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str
    login: str
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt
    profile_url: str | list[str]


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
    login: str | None = None
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt | None = None
    profile_url: str | list[str] | None = None
