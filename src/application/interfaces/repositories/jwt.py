from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from src.application.dto import RefreshToken


class IJWTRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, refresh_token: RefreshToken) -> None:
        pass

    @abstractmethod
    async def get_device_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshToken]:
        pass

    @abstractmethod
    async def mark_tokens_as_compromised(
        self, user_id: UUID, fingerprint: str, time_revealed: datetime
    ) -> Any:
        pass
