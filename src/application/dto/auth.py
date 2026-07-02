import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Self
from uuid import UUID

from src.application.dto.token import TokenStatus

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class User:
    """Authenticated user data retrieved from storage."""

    user_id: UUID
    user_name: str
    is_active: bool
    is_verified: bool

    is_superuser: bool = False
    hashed_password: str | None = None


@dataclass(slots=True)
class UserPayload:
    """Minimal user payload for embedding into JWT tokens."""

    user_id: UUID
    is_superuser: bool
    provider: str = "local"
    exp: datetime | None = None

    def to_payload(self) -> dict:
        return dict(
            user_id=str(self.user_id),
            is_superuser=self.is_superuser,
            exp=self.exp,
            provider=self.provider,
        )

    @classmethod
    def create(
        cls,
        user_id: UUID | str,
        is_superuser: bool = False,
        provider: str = "local",
        exp: datetime | int | None = None,
    ) -> Self:
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                logger.exception(
                    "Unable to convert user_id to UUID, invalid ID provided, %s",
                    user_id,
                )
                raise

        if isinstance(exp, int):
            try:
                exp = datetime.fromtimestamp(exp, tz=timezone.utc)
            except ValueError:
                logger.exception(
                    "Unable to convert exp to datetime, "
                    "invalid epoch value provided, %s",
                    exp,
                )
                raise

        return cls(
            user_id=user_id,
            is_superuser=is_superuser,
            exp=exp,
            provider=provider,
        )


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str


@dataclass(slots=True)
class RefreshTokenRecord:
    """Refresh token data for persistence."""

    user_id: UUID
    hashed_token: str
    expires_at: datetime
    status_id: int = TokenStatus.ACTIVE
    hashed_fingerprint: str | None = None
