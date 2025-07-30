from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Identity,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .cheatsheet_stats import CheatsheetStats
    from .cheatsheet_to_tag import CheatsheetToTag


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
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    stats: Mapped["CheatsheetStats"] = relationship(
        back_populates="cheatsheet",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )

    tags_association: Mapped[list["CheatsheetToTag"]] = relationship(
        back_populates="cheatsheet", cascade="all, delete-orphan"
    )
