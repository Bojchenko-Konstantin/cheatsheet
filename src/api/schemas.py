import re
from datetime import datetime
from typing import Annotated, Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictBool, model_validator

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

    @model_validator(mode="before")
    @classmethod
    def flatten_stats(cls, data: Any) -> Any:
        """Flatten CheatsheetStats into top-level count_like/count_view fields."""
        if isinstance(data, dict):
            stats = data.pop("stats", {})
            if isinstance(stats, dict):
                data["count_like"] = stats.get("count_like", 0)
                data["count_view"] = stats.get("count_view", 0)
            data.pop("user_id", None)
        elif hasattr(data, "stats"):
            data = {
                "cheatsheet_id": data.cheatsheet_id,
                "title": data.title,
                "content": data.content,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "is_public": data.is_public,
                "tags": data.tags,
                "count_like": data.stats.count_like,
                "count_view": data.stats.count_view,
            }
        return data

    @model_validator(mode="after")
    def sort_tags(self) -> Self:
        self.tags.sort(key=lambda x: x.tag_id)
        return self


class CheatsheetListRead(Schema):
    items: list[CheatsheetRead]
    next_cursor: str | None
    previous_cursor: str | None
    has_next: bool
    has_previous: bool


class SearchSuggestionsRead(Schema):
    titles: list[str]
    tags: list[str]


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
    def validate_password_strength(self) -> Self:
        _validate_password_strength(self.password)
        return self

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


class Token(Schema):
    access_token: str
    token_type: str = "bearer"


class TokenVerification(Schema):
    fingerprint: str


class LogoutRequest(Schema):
    fingerprint: str


class PasswordResetRequest(Schema):
    email: EmailStr


class PasswordResetConfirm(Schema):
    token: str
    new_password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: str

    @model_validator(mode="after")
    def validate_password_strength(self) -> Self:
        _validate_password_strength(self.new_password)
        return self

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class PasswordResetResponse(Schema):
    message: str = "If the email exists, a password reset link has been sent."


class PasswordUpdate(Schema):
    old_password: str
    new_password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: str

    @model_validator(mode="after")
    def validate_password_strength(self) -> Self:
        _validate_password_strength(self.new_password)
        return self

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class PasswordUpdateResponse(Schema):
    message: str = "Password has been successfully changed."


class EmailVerificationConfirm(Schema):
    token: str


class EmailVerificationResponse(Schema):
    message: str = "Email has been successfully verified."


class EmailVerificationSendResponse(Schema):
    message: str = "If the email is not verified, a verification link has been sent."


def _validate_password_strength(password: str) -> None:
    """Validate password strength requirements."""
    is_password_valid = all(
        [
            len(password) > 8,  # greater than 8 symbols
            re.search(r"\d", password),  # at least 1 digit
            re.search(r"[A-Z]", password),  # at least 1 capital letter
            re.search(r"[^\w\s]", password),  # at least 1 punctuation symbol
        ]
    )

    if not is_password_valid:
        raise ValueError(
            "Your password is weak. It must be greater than 8 symbols "
            "and contain at least 1 digit, 1 punctuation symbol "
            "and 1 capital letter."
        )


class OAuthCallbackParams(Schema):
    code: str
    state: str
    cid: str | None = None
    error: str | None = None
    error_description: str | None = None
