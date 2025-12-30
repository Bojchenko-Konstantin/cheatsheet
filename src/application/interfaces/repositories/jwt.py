from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.application.dto import RefreshToken


class IJWTRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, refresh_token: RefreshToken) -> None:
        pass

    @abstractmethod
    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshToken:
        pass

    @abstractmethod
    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshToken] | None:
        pass

    @abstractmethod
    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str) -> Any:
        pass
