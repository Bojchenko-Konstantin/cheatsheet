from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    DateTime,
    ForeignKey,
    SmallInteger,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        OAuthAccountModel,
        RefreshTokenStatusModel,
    )


class OAuthRefreshTokenModel(Base):
    __tablename__ = "oauth_refresh_token"  # type: ignore[assignment]

    refresh_token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=func.uuid_generate_v7(),
        primary_key=True,
    )
    oauth_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oauth_account.oauth_account_id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("md_refresh_token_status.status_id", ondelete="RESTRICT"),
        nullable=False,
        server_default="1",
    )
    hashed_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status_name: Mapped[RefreshTokenStatusModel] = relationship(
        back_populates="oauth_refresh_tokens",
    )
    oauth_account: Mapped[OAuthAccountModel] = relationship(
        back_populates="refresh_tokens"
    )
