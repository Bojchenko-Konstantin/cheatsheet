from src.application.dto import (
    EmailVerificationData,
    PasswordResetEmailData,
    WelcomeEmailData,
)
from src.application.interfaces.services import (
    IEmailTemplateService,
    INotificationService,
)


class NotificationUseCase:
    """Use case for sending notifications."""

    def __init__(
        self,
        notification_service: INotificationService,
        template_service: IEmailTemplateService,
    ) -> None:
        self._notification_service = notification_service
        self._template_service = template_service

    async def send_welcome_email(self, data: WelcomeEmailData) -> None:
        """Send welcome email to newly registered user."""
        email_message = self._template_service.generate_welcome_email(data)
        await self._notification_service.send_email(email_message)

    async def send_password_reset_email(self, data: PasswordResetEmailData) -> None:
        """Send password reset email with token link."""
        email_message = self._template_service.generate_password_reset_email(data)
        await self._notification_service.send_email(email_message)

    async def send_password_changed_email(
        self, email: str, user_name: str, display_name: str | None = None
    ) -> None:
        """Send confirmation email after successful password change."""
        email_message = self._template_service.generate_password_changed_email(
            email, user_name, display_name
        )
        await self._notification_service.send_email(email_message)

    async def send_email_verification(self, data: EmailVerificationData) -> None:
        """Send email verification message with token link."""
        email_message = self._template_service.generate_email_verification(data)
        await self._notification_service.send_email(email_message)
