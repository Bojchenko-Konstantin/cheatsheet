from src.application.dto import WelcomeEmailData
from src.application.use_cases.notification import NotificationUseCase
from src.infrastructure.broker import BROKER
from src.infrastructure.email_template_service import EmailTemplateService
from src.infrastructure.notification_service import NotiSendNotificationService


@BROKER.task(retry_on_error=True)
async def send_welcome_email(email: str, user_name: str | None) -> None:
    """Send welcome email to new user. Failure doesn't affect registration."""
    notification_service = NotiSendNotificationService()
    email_template_service = EmailTemplateService()
    notification_use_case = NotificationUseCase(
        notification_service, email_template_service
    )

    if not user_name:
        user_name = email.rsplit("@", 1)[0]

    welcome_data = WelcomeEmailData(
        email=email,
        user_name=user_name,
    )
    await notification_use_case.send_welcome_email(welcome_data)
