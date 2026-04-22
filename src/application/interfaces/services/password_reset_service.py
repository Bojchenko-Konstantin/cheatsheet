from abc import ABC, abstractmethod
from uuid import UUID

from src.application.dto import PasswordResetTokenPayload


class IPasswordResetService(ABC):
    """Handles password reset token generation and verification."""

    @abstractmethod
    def generate_reset_token(self, user_id: UUID, email: str) -> str:
        """Generate a stateless JWT token for password reset."""
        pass

    @abstractmethod
    def verify_reset_token(self, token: str) -> PasswordResetTokenPayload:
        """Verify and decode a password reset token."""
        pass

    @abstractmethod
    def get_reset_url(self, token: str) -> str:
        """Build the full password reset URL with token."""
        pass
