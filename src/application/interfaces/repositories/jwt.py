from abc import ABC, abstractmethod
from datetime import datetime


class IJWTRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def save(self, token_hash: str, expires_at: datetime) -> None:
        pass
