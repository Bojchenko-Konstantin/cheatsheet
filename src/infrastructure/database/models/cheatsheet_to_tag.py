from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import CheatsheetModel, TagModel


class CheatsheetToTagModel(Base):
    cheatsheet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cheatsheet.cheatsheet_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("md_tag.tag_id", ondelete="CASCADE"),
        primary_key=True,
    )
    cheatsheet: Mapped[CheatsheetModel] = relationship(
        back_populates="tag_associations"
    )
    tag: Mapped[TagModel] = relationship(back_populates="cheatsheet_associations")
