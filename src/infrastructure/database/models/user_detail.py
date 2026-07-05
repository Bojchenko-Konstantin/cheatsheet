from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        SocialNetworkModel,
        UserModel,
        UserToSocialNetworkModel,
    )


class UserDetailModel(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    last_name: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    profile_description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
    )
    user: Mapped[UserModel] = relationship(back_populates="detail")
    social_network_associations: Mapped[list[UserToSocialNetworkModel]] = relationship(
        back_populates="user_detail",
        cascade="all, delete-orphan",
    )
    social_networks: Mapped[list[SocialNetworkModel]] = relationship(
        secondary="user_to_social_network",
        back_populates="user_details",
        viewonly=True,
    )
    __table_args__ = (
        CheckConstraint("first_name != ''", name="ck_first_name_not_empty"),
        CheckConstraint("last_name != ''", name="ck_last_name_not_empty"),
        CheckConstraint(
            "profile_description != ''", name="ck_profile_description_not_empty"
        ),
    )
