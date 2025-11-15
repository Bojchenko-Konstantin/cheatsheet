from abc import ABC, abstractmethod
from typing import Any

from src.application.dto import User, UserPayload


class IUserRepo(ABC):
    """Abstract class for operations with user storage."""

    @abstractmethod
    async def get_by_user_name(self, user_name: str) -> User:
        pass

    @abstractmethod
    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        pass

    @abstractmethod
    async def update(self, update_data: dict[str, Any]):
        pass
