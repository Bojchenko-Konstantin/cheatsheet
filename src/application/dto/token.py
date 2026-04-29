from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from uuid import UUID


class TokenStatus(IntEnum):
    ACTIVE = 1
    REVOKED = 2
    EXPIRED = 3
    COMPROMISED = 4


@dataclass(slots=True)
class EmailVerificationTokenPayload:
    """Payload decoded from verified email verification token."""

    user_id: UUID
    email: str
    exp: datetime
