from src.application.dto import WelcomeEmailData
from src.application.email_template_service import EmailTemplateService
from src.application.interfaces.notification_service import INotificationService


class NotificationUseCase:
    """Use case for sending notifications."""

    def __init__(
        self,
        notification_service: INotificationService,
        template_service: EmailTemplateService | None = None,
    ) -> None:
        self._notification_service = notification_service
        self._template_service = template_service or EmailTemplateService()

    async def send_welcome_email(self, data: WelcomeEmailData) -> None:
        """Send welcome email to newly registered user."""
        email_message = self._template_service.create_welcome_email(data)
        await self._notification_service.send_email(email_message)
