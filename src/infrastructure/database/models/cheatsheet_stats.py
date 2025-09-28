from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, BigInteger, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .cheatsheet import CheatsheetModel


class CheatsheetStatsModel(Base):
    cheatsheet_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("cheatsheet.cheatsheet_id", ondelete="CASCADE"),
        primary_key=True,
    )
    count_like: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )
    count_view: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )

    cheatsheet: Mapped[CheatsheetModel] = relationship(back_populates="stats")

    __table_args__ = (
        CheckConstraint("count_like >= 0", name="ck_count_like_positive"),
        CheckConstraint("count_view >= 0", name="ck_count_view_positive"),
    )
