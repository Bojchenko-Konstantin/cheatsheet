from abc import ABC, abstractmethod
from uuid import UUID

from src.application.dto import TokenPair, UserPayload


class ITokenService(ABC):
    """Handles all operations with tokens."""

    @abstractmethod
    async def generate_tokens(self, payload: UserPayload) -> TokenPair:
        """Generate access and refresh token pair."""
        pass

    @abstractmethod
    async def verify_access_token(self, access_token: str) -> UserPayload:
        """Verify and decode an access token."""
        pass

    @abstractmethod
    async def verify_refresh_token(
        self, plain_token: str, hashed_fingerprint: str
    ) -> UserPayload:
        """Verify refresh token validity and detect token reuse."""
        pass

    @abstractmethod
    async def revoke_refresh_token(
        self, plain_token: str, hashed_fingerprint: str
    ) -> None:
        """Revoke a specific refresh token."""
        pass

    @abstractmethod
    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke all active refresh tokens for a user."""
        pass
