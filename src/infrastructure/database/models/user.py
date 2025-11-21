from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models import Base
from src.infrastructure.database.models.refresh_token import RefreshTokenModel

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        CheatsheetModel,
        RefreshTokenModel,
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
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cheatsheets: Mapped[list[CheatsheetModel]] = relationship(back_populates="user")
    detail: Mapped[UserDetailModel] = relationship(back_populates="user")
    refresh_tokens: Mapped[list[RefreshTokenModel]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
