from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.application.dto import PasswordResetData, User, UserPayload


class IUserService(ABC):
    """Service for user management operations."""

    @abstractmethod
    async def get_by_user_name(self, user_name: str) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> PasswordResetData | None:
        pass

    @abstractmethod
    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        pass

    @abstractmethod
    async def authenticate_user(self, user_name: str, password: str) -> User:
        pass

    @abstractmethod
    async def update_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        """
        Change password for authenticated user.
        Verifies old password before updating.
        """
        pass

    @abstractmethod
    async def reset_password(self, user_id: UUID, new_password: str) -> None:
        """
        Reset password without requiring old password.
        Used after successful password reset token verification.
        """
        pass
