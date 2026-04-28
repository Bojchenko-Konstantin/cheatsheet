from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.application.dto import RefreshTokenRecord


class ITokenRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, token_record: RefreshTokenRecord) -> None:
        pass

    @abstractmethod
    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshTokenRecord:
        """Retrieve the current active refresh token for a specific device."""
        pass

    @abstractmethod
    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshTokenRecord] | None:
        """Retrieve all revoked or expired tokens for a device family."""
        pass

    @abstractmethod
    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str) -> Any:
        """Mark all tokens in the device family as compromised."""
        pass

    @abstractmethod
    async def revoke_token(
        self, user_id: UUID, fingerprint: str, hashed_token: str
    ) -> None:
        """Revoke a specific active refresh token."""
        pass

    @abstractmethod
    async def revoke_all_tokens_for_user(self, user_id: UUID) -> None:
        """Revoke all active refresh tokens for a user."""
        pass
