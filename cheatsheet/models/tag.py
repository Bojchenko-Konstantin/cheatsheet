from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .cheatsheet_to_tag import CheatsheetToTag


class Tag(Base):
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

    cheatsheets_association: Mapped[list["CheatsheetToTag"]] = relationship(
        back_populates="tag"
    )
