from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .cheatsheet import Cheatsheet
    from .tag import Tag


class CheatsheetToTag(Base):
    __tablename__ = "cheatsheet_to_tag"  # type: ignore[assignment]

    cheatsheet_id: Mapped[int] = mapped_column(
        ForeignKey("cheatsheet.cheatsheet_id"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("md_tag.tag_id"),
        primary_key=True,
    )

    cheatsheet: Mapped["Cheatsheet"] = relationship(back_populates="tags_association")
    tag: Mapped["Tag"] = relationship(back_populates="cheatsheets_association")
