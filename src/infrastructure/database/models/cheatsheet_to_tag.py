from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .cheatsheet import CheatsheetModel
    from .tag import TagModel


class CheatsheetToTagModel(Base):

    cheatsheet_id: Mapped[int] = mapped_column(
        ForeignKey("cheatsheet.cheatsheet_id"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("md_tag.tag_id"),
        primary_key=True,
    )

    cheatsheet: Mapped["CheatsheetModel"] = relationship(
        back_populates="tags_association"
    )
    tag: Mapped["TagModel"] = relationship(back_populates="cheatsheets_association")
