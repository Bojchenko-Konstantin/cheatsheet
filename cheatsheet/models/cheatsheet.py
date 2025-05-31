from datetime import datetime
from typing import List

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    String,
    Text,
)

# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .tag import Tag

# from uuid_extensions import uuid7


class Cheatsheet(Base):
    cheatsheet_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        server_default=Identity(always=True),
    )
    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )
    count_like: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default="0",
    )
    count_view: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default="0",
    )
    # user_id: Mapped[UUID] = mapped_column(
    #     UUID(as_uuid=True),
    #     ForeignKey("user.id"),
    #     default=uuid7,
    #     nullable=False,
    # )
    #
    # user: Mapped["User"] = relationship(
    #     back_populates="cheatsheet"
    # )
    tags: Mapped[List["Tag"]] = relationship(
        secondary="cheatsheet_to_tag",
        back_populates="cheatsheet",
    )

    __table_args__ = (
        CheckConstraint("count_like >= 0", name="ck_count_like_positive"),
        CheckConstraint("count_view >= 0", name="ck_count_view_positive"),
    )
