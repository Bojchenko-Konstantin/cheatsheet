from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.user import UserModel


class UserDetailModel(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    profile_description: Mapped[str] = mapped_column(
        Text,
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
    )
    user: Mapped[UserModel] = relationship(back_populates="detail")
