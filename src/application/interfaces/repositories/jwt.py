from abc import ABC, abstractmethod

from src.application.dto import RefreshToken


class IJWTRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, refresh_token: RefreshToken) -> None:
        pass
