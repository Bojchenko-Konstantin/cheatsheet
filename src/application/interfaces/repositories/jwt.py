from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.application.dto import RefreshTokenRecord


class IJWTRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, token_record: RefreshTokenRecord) -> None:
        pass

    @abstractmethod
    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshTokenRecord:
        pass

    @abstractmethod
    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshTokenRecord] | None:
        pass

    @abstractmethod
    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str) -> Any:
        pass
