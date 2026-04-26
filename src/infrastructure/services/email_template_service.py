from datetime import datetime

from src.application.dto import (
    EmailMessage,
    EmailType,
    EmailVerificationData,
    PasswordResetEmailData,
    WelcomeEmailData,
)
from src.application.email_templates import (
    EMAIL_VERIFICATION_SUBJECT,
    EMAIL_VERIFICATION_TEMPLATE,
    PASSWORD_CHANGED_EMAIL_SUBJECT,
    PASSWORD_CHANGED_EMAIL_TEMPLATE,
    PASSWORD_RESET_EMAIL_SUBJECT,
    PASSWORD_RESET_EMAIL_TEMPLATE,
    WELCOME_EMAIL_SUBJECT,
    WELCOME_EMAIL_TEMPLATE,
)
from src.application.interfaces import IEmailTemplateService
from src.core.config import settings


class EmailTemplateService(IEmailTemplateService):
    """Service for generating email content from templates."""

    def __init__(self) -> None:
        self._app_name = "Cheatsheet App"
        self._support_email = settings.notisend.from_email

    def generate_welcome_email(self, data: WelcomeEmailData) -> EmailMessage:
        """Create welcome email for new users."""
        display_name = data.get_display_name()

        text = WELCOME_EMAIL_TEMPLATE.format(
            display_name=display_name,
            username=data.user_name,
            support_email=self._support_email,
        )

        return EmailMessage(
            to=data.email,
            subject=WELCOME_EMAIL_SUBJECT,
            text=text,
            email_type=EmailType.WELCOME,
        )

    def generate_password_reset_email(
        self, data: PasswordResetEmailData, expires_in_minutes: int
    ) -> EmailMessage:
        """Create password reset email."""
        display_name = data.get_display_name()

        text = PASSWORD_RESET_EMAIL_TEMPLATE.format(
            display_name=display_name,
            reset_url=data.reset_url,
            expires_in_minutes=expires_in_minutes,
            support_email=self._support_email,
        )

        return EmailMessage(
            to=data.email,
            subject=PASSWORD_RESET_EMAIL_SUBJECT,
            text=text,
            email_type=EmailType.PASSWORD_RESET,
        )

    def generate_password_changed_email(
        self, email: str, user_name: str, display_name: str | None = None
    ) -> EmailMessage:
        """Create password changed confirmation email."""
        name_for_display = display_name or user_name
        change_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        text = PASSWORD_CHANGED_EMAIL_TEMPLATE.format(
            display_name=name_for_display,
            username=user_name,
            change_time=change_time,
            support_email=self._support_email,
        )

        return EmailMessage(
            to=email,
            subject=PASSWORD_CHANGED_EMAIL_SUBJECT,
            text=text,
            email_type=EmailType.PASSWORD_CHANGED,
        )

    def generate_email_verification(
        self, data: EmailVerificationData, expires_in_minutes: int
    ) -> EmailMessage:
        """Create email verification message with token link."""
        display_name = data.get_display_name()

        text = EMAIL_VERIFICATION_TEMPLATE.format(
            display_name=display_name,
            verification_url=data.verification_url,
            expires_in_minutes=expires_in_minutes,
            support_email=self._support_email,
        )

        return EmailMessage(
            to=data.email,
            subject=EMAIL_VERIFICATION_SUBJECT,
            text=text,
            email_type=EmailType.EMAIL_VERIFICATION,
        )
