from abc import ABC, abstractmethod
from typing import Any


class IUserRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def get_by_user_name(self, user_name: str) -> dict:
        pass

    @abstractmethod
    async def create(self, create_data: dict[str, Any]):
        pass

    @abstractmethod
    async def update(self, update_data: dict[str, Any]):
        pass
