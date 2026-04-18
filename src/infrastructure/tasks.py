from src.application.dto import WelcomeEmailData
from src.application.use_cases.notification import NotificationUseCase
from src.infrastructure.broker import BROKER


@BROKER.task(retry_on_error=True)
async def send_welcome_email(
    email: str, user_name: str | None, notification_use_case: NotificationUseCase
) -> None:
    """Send welcome email to new user. Failure doesn't affect registration."""
    if not user_name:
        user_name = email.rsplit("@", 1)[0]

    welcome_data = WelcomeEmailData(
        email=email,
        user_name=user_name,
    )
    await notification_use_case.send_welcome_email(welcome_data)
