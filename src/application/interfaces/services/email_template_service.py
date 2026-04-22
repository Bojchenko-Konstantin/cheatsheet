from abc import ABC, abstractmethod

from src.application.dto import EmailMessage, PasswordResetEmailData, WelcomeEmailData


class IEmailTemplateService(ABC):
    """Email content generator interface."""

    @abstractmethod
    def generate_welcome_email(self, data: WelcomeEmailData) -> EmailMessage:
        pass

    @abstractmethod
    def generate_password_reset_email(
        self, data: PasswordResetEmailData, expires_in_minutes: int = 30
    ) -> EmailMessage:
        pass

    @abstractmethod
    def generate_password_changed_email(
        self, email: str, user_name: str, display_name: str | None = None
    ) -> EmailMessage:
        pass
