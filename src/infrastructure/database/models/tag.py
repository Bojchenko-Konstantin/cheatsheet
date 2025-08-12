from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Identity,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .cheatsheet_to_tag import CheatsheetToTagModel


class TagModel(Base):
    __tablename__ = "md_tag"  # type: ignore[assignment]

    tag_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        server_default=Identity(always=True),
    )
    tag_name: Mapped[str] = mapped_column(
        String(35),
        nullable=False,
        unique=True,
    )

    cheatsheets_association: Mapped[list[CheatsheetToTagModel]] = relationship(
        back_populates="tag"
    )

    __table_args__ = (
        CheckConstraint("LENGTH(TRIM(tag_name)) > 0", name="ck_tag_name_non_empty"),
        Index("ix_tag_name_lower", func.lower(tag_name), unique=True),
    )
