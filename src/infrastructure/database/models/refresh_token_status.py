from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Identity,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models import (
    Base,
    RefreshTokenBlacklistModel,
    RefreshTokenModel,
)

if TYPE_CHECKING:
    from src.infrastructure.database.models import RefreshTokenModel


class RefreshTokenStatusModel(Base):
    __tablename__ = "md_refresh_token_status"  # type: ignore[assignment]

    status_id: Mapped[int] = mapped_column(
        SmallInteger,
        Identity(always=True),
        primary_key=True,
    )
    status_name: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )
    refresh_tokens: Mapped[list[RefreshTokenModel]] = relationship(
        "RefreshTokenModel",
        back_populates="status_name",
        cascade="all, delete-orphan",
    )
    blacklisted_refresh_tokens: Mapped[list[RefreshTokenBlacklistModel]] = relationship(
        "RefreshTokenBlacklistModel",
        back_populates="status_name",
        cascade="all, delete-orphan",
    )
