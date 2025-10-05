from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table

from .base import Base

cheatsheet_to_tag_association = Table(
    "cheatsheet_to_tag",
    Base.metadata,
    Column(
        "cheatsheet_id",
        ForeignKey("cheatsheet.cheatsheet_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("md_tag.tag_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
