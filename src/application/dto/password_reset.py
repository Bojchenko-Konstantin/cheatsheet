from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class PasswordResetTokenPayload:
    """Payload decoded from verified reset token."""

    user_id: UUID
    email: str
    exp: datetime


@dataclass(slots=True)
class PasswordResetData:
    """User data returned after email lookup for reset."""

    user_id: UUID
    user_name: str
    email: str
