import logging
from collections.abc import MutableMapping
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import IntEnum
from typing import Self
from uuid import UUID

logger = logging.getLogger(__name__)


class TokenStatus(IntEnum):
    ACTIVE = 1
    REVOKED = 2
    EXPIRED = 3
    COMPROMISED = 4


@dataclass(slots=True)
class User:
    user_id: UUID
    user_name: str
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool

    @classmethod
    def from_dict(cls, kwargs: MutableMapping) -> Self:
        return cls(**kwargs)


@dataclass(slots=True)
class UserPayload:
    user_id: str
    is_superuser: bool
    exp: datetime | None = None

    @classmethod
    def from_dict(cls, kwargs: MutableMapping) -> Self:
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RefreshToken:
    user_id: str | UUID
    hashed_token: str
    expires_at: datetime
    status_id: int = TokenStatus.ACTIVE
    hashed_fingerprint: str | None = None

    def __post_init__(self):
        if not isinstance(self.user_id, UUID):
            try:
                self.user_id = UUID(self.user_id)
            except ValueError:
                logger.exception(
                    "Unable to convert user_id to UUID, invalid id provided: %s",
                    self.user_id,
                )
                raise

    @classmethod
    def from_dict(cls, kwargs: MutableMapping) -> Self:
        return cls(**kwargs)
