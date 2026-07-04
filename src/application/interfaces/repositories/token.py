from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.application.dto import RefreshTokenRecord, UserPayload


class ITokenRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, token_record: RefreshTokenRecord) -> None:
        pass

    @abstractmethod
    async def get_user_payload_by_hash(
        self, hashed_token: str, fingerprint: str
    ) -> UserPayload | None:
        """Retrieve the current active refresh token."""
        pass

    @abstractmethod
    async def is_token_in_blacklist(self, hashed_token: str, fingerprint: str) -> bool:
        """Retrieve all revoked or expired tokens for a device family."""
        pass

    @abstractmethod
    async def mark_as_compromised(self, hashed_token: str, fingerprint: str) -> Any:
        """Mark all tokens in the device family as compromised."""
        pass

    @abstractmethod
    async def revoke_token(self, hashed_token: str, fingerprint: str) -> None:
        """Revoke a specific active refresh token."""
        pass

    @abstractmethod
    async def revoke_all_tokens(self, user_id: UUID) -> None:
        """Revoke all active refresh tokens for a user."""
        pass
