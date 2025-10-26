from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        CheatsheetStatsModel,
        CheatsheetToTagModel,
        TagModel,
    )


class CheatsheetModel(Base):
    cheatsheet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=func.uuid_generate_v7(),
        primary_key=True,
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
    stats: Mapped[CheatsheetStatsModel] = relationship(
        back_populates="cheatsheet",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    tags: Mapped[list["TagModel"]] = relationship(
        secondary="cheatsheet_to_tag",
        back_populates="cheatsheets",
        viewonly=True,
    )
    tag_associations: Mapped[list["CheatsheetToTagModel"]] = relationship(
        back_populates="cheatsheet"
    )
