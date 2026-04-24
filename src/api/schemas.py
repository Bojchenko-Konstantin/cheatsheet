from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictBool, model_validator

from src.application.exceptions import PasswordsNotMatchError

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
    tag_id: PositiveInt


class Tag(TagBase):
    tag_name: Annotated[str, Field(max_length=35)]


class CheatsheetBase(Schema):
    tags: list[Tag]
    title: Title
    is_public: StrictBool
    content: str


class CheatsheetRead(Schema):
    cheatsheet_id: UUID
    title: Title
    content: str
    created_at: datetime
    updated_at: datetime
    is_public: StrictBool
    tags: list[Tag]
    count_like: PositiveInt
    count_view: PositiveInt

    @model_validator(mode="after")
    def sort_tags(self) -> Self:
        self.tags.sort(key=lambda x: x.tag_id)
        return self


class CheatsheetCreate(CheatsheetBase):
    pass


class CheatsheetUpdate(CheatsheetBase):
    pass


class CheatsheetUpdatePartial(Schema):
    tag_ids: TagList | None = None
    title: Title | None = None
    is_public: StrictBool | None = None
    content: str | None = None


class UserBase(Schema):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt
    network_url: list[str]


class UserRead(UserBase):
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    user_id: UUID


class UserCreate(UserBase):
    password: str
    password_confirmation: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match")

        return self


class UserUpdate(Schema):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    profile_description: str | None = None
    image_url: str | None = None
    social_network_id: PositiveListInt | None = None
    network_url: list[str] | None = None


class TokenPair(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenVerification(Schema):
    refresh_token: str
    fingerprint: str
    user_id: UUID


class LogoutRequest(Schema):
    user_id: UUID
    refresh_token: str
    fingerprint: str


class PasswordResetRequest(Schema):
    email: EmailStr


class PasswordResetConfirm(Schema):
    token: str
    new_password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise PasswordsNotMatchError
        return self


class PasswordResetResponse(Schema):
    message: str = "If the email exists, a password reset link has been sent."


class PasswordUpdate(Schema):
    old_password: str
    new_password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise PasswordsNotMatchError
        return self


class PasswordUpdateResponse(Schema):
    message: str = "Password has been successfully changed."
