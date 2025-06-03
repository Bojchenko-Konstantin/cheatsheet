from typing import Annotated

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
