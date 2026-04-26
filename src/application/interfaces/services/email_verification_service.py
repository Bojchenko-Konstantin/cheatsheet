from abc import ABC, abstractmethod
from uuid import UUID

from src.application.dto import EmailVerificationTokenPayload


class IEmailVerificationService(ABC):
    """Handles email verification token generation and verification."""

    @abstractmethod
    def generate_verification_token(self, user_id: UUID, email: str) -> str:
        """Generate a stateless JWT token for email verification."""
        pass

    @abstractmethod
    def verify_verification_token(self, token: str) -> EmailVerificationTokenPayload:
        """Verify and decode an email verification token."""
        pass

    @abstractmethod
    def get_verification_url(self, token: str) -> str:
        """Build the full email verification URL with token."""
        pass
