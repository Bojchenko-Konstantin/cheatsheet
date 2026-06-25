from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import UserModel


class RegisteredUserModel(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024),
        nullable=False,
    )
    user: Mapped[UserModel] = relationship(back_populates="registered_user")
