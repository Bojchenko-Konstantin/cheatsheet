from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models import SocialNetworkModel, UserDetailModel


class UserDetailToSocialNetworkModel(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_detail.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    social_network_id: Mapped[int] = mapped_column(
        ForeignKey("md_social_network.social_network_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_detail: Mapped[UserDetailModel] = relationship(
        back_populates="social_network_associations",
    )
    social_network: Mapped[SocialNetworkModel] = relationship(
        back_populates="user_detail_associations",
    )
