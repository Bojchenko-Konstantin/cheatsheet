from src.application.dto import PasswordResetEmailData, WelcomeEmailData
from src.application.use_cases.notification import NotificationUseCase
from src.infrastructure.background_tasks.broker import BROKER
from src.infrastructure.services import (
    EmailTemplateService,
    NotiSendNotificationService,
)


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


@BROKER.task(retry_on_error=True)
async def send_password_reset_email(
    email: str, user_name: str, reset_url: str, expires_in_minutes: int = 30
) -> None:
    """Send password reset email with token link. Failure allows user to retry."""
    email_template_service = EmailTemplateService()
    notification_service = NotiSendNotificationService()

    email_data = PasswordResetEmailData(
        email=email,
        user_name=user_name,
        reset_url=reset_url,
    )

    email_message = email_template_service.generate_password_reset_email(
        email_data,
        expires_in_minutes=expires_in_minutes,
    )

    await notification_service.send_email(email_message)


@BROKER.task(retry_on_error=True)
async def send_password_changed_email(email: str, user_name: str) -> None:
    """Send password changed confirmation email."""
    email_template_service = EmailTemplateService()
    notification_service = NotiSendNotificationService()

    email_message = email_template_service.generate_password_changed_email(
        email=email,
        user_name=user_name,
    )

    await notification_service.send_email(email_message)
