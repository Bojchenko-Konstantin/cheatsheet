from abc import ABC, abstractmethod
from uuid import UUID

from src.application.dto import UserPayload


class ITokenService(ABC):
    """Handles all operations with tokens."""

    @abstractmethod
    async def generate_tokens(self, payload: UserPayload) -> dict[str, str]:
        pass

    @abstractmethod
    async def verify_access_token(self, access_token: str) -> UserPayload:
        pass

    @abstractmethod
    async def verify_refresh_token(
        self, user_id: UUID, plain_refresh_token: str, fingerprint: str
    ) -> None:
        pass

    @abstractmethod
    async def revoke_refresh_token(
        self, user_id: UUID, plain_refresh_token: str, fingerprint: str
    ) -> None:
        pass

    @abstractmethod
    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        pass
