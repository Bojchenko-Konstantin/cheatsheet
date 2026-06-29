from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import UserModel


class OAuthAccountModel(Base):
    __tablename__ = "oauth_account"  # type: ignore[assignment]

    oauth_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=func.uuid_generate_v7(),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_user_id: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    provider_psuid: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    oauth_service_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("md_oauth_service.oauth_service_id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[UserModel] = relationship(back_populates="oauth_accounts")
    __table_args__ = (
        UniqueConstraint(
            "oauth_service_id", "provider_user_id", name="uq_oauth_service_provider"
        ),
        UniqueConstraint("user_id", "oauth_service_id", name="uq_user_oauth_service"),
    )
