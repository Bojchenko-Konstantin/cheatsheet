from abc import ABC, abstractmethod
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
