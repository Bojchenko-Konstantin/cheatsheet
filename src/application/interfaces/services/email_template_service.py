from abc import ABC, abstractmethod

from src.application.dto import (
    EmailMessage,
    EmailVerificationData,
    PasswordResetEmailData,
    WelcomeEmailData,
)


class IEmailTemplateService(ABC):
    """Email content generator interface."""

    @abstractmethod
    def generate_welcome_email(self, data: WelcomeEmailData) -> EmailMessage:
        """Generate welcome email for newly registered users."""
        pass

    @abstractmethod
    def generate_password_reset_email(
        self, data: PasswordResetEmailData, expires_in_minutes: int
    ) -> EmailMessage:
        """Generate password reset email with token link."""
        pass

    @abstractmethod
    def generate_password_changed_email(
        self, email: str, user_name: str, display_name: str | None = None
    ) -> EmailMessage:
        """Generate confirmation email after successful password reset."""

    @abstractmethod
    def generate_email_verification(
        self, data: EmailVerificationData, expires_in_minutes: int
    ) -> EmailMessage:
        """Generate email verification message with token link."""
        pass
