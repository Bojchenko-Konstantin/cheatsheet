from __future__ import annotations

from sqlalchemy import CheckConstraint, Identity, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models import Base


class OAuthServiceModel(Base):
    __tablename__ = "md_oauth_service"  # type: ignore[assignment]

    oauth_service_id: Mapped[int] = mapped_column(
        SmallInteger,
        primary_key=True,
        server_default=Identity(always=True),
    )
    oauth_service_name: Mapped[str] = mapped_column(
        String(35),
        nullable=False,
        unique=True,
    )

    __table_args__ = (
        CheckConstraint(
            "LENGTH(TRIM(oauth_service_name)) > 0",
            name="ck_oauth_service_name_non_empty",
        ),
    )
