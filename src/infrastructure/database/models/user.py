from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models import (
    Base,
    OAuthAccountModel,
    RefreshTokenBlacklistModel,
    RefreshTokenModel,
)

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        CheatsheetModel,
        RefreshTokenModel,
        RegisteredUserModel,
        UserDetailModel,
    )


class UserModel(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=func.uuid_generate_v7(),
        primary_key=True,
    )
    user_name: Mapped[str] = mapped_column(
        String(length=25),
        nullable=False,
        unique=True,
    )
    email: Mapped[str] = mapped_column(
        String(length=320),
        nullable=False,
        unique=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    cheatsheets: Mapped[list[CheatsheetModel]] = relationship(back_populates="user")
    detail: Mapped[UserDetailModel] = relationship(back_populates="user")
    refresh_tokens: Mapped[list[RefreshTokenModel]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    blacklisted_tokens: Mapped[list[RefreshTokenBlacklistModel]] = relationship(
        "RefreshTokenBlacklistModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    registered_user: Mapped[RegisteredUserModel] = relationship(back_populates="user")
    oauth_account: Mapped[OAuthAccountModel] = relationship(back_populates="user")
