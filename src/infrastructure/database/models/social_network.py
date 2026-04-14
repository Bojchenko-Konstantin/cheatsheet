from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Identity,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        UserDetailModel,
        UserToSocialNetworkModel,
    )


class SocialNetworkModel(Base):
    __tablename__ = "md_social_network"  # type: ignore[assignment]

    social_network_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        server_default=Identity(always=True),
    )
    network_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )
    network_image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    user_detail_associations: Mapped[list[UserToSocialNetworkModel]] = relationship(
        back_populates="social_network"
    )
    user_details: Mapped[list[UserDetailModel]] = relationship(
        secondary="user_to_social_network",
        back_populates="social_networks",
        viewonly=True,
    )
