from src.application.dto import WelcomeEmailData
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
