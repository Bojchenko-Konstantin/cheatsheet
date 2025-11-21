from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import RefreshTokenStatusModel, UserModel


class RefreshTokenModel(Base):
    refresh_token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=func.uuid_generate_v7(),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("md_refresh_token_status.status_id", ondelete="RESTRICT"),
        nullable=False,
        server_default="1",
    )
    hashed_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    hashed_fingerprint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="refresh_tokens",
    )
    status: Mapped[RefreshTokenStatusModel] = relationship(
        "RefreshTokenStatusModel",
        back_populates="refresh_tokens",
    )
