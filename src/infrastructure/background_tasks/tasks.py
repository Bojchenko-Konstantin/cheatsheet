from typing import Annotated

from taskiq import Context, TaskiqDepends, async_shared_broker

from src.application.dto import (
    EmailVerificationData,
    PasswordResetEmailData,
    WelcomeEmailData,
)


@async_shared_broker.task(retry_on_error=True)
async def send_welcome_email(
    email: str,
    user_name: str | None,
    context: Annotated[Context, TaskiqDepends()],
) -> None:
    """Send welcome email to new user. Failure doesn't affect registration."""
    notification_use_case = context.state.notification_use_case

    if not user_name:
        user_name = email.rsplit("@", 1)[0]

    welcome_data = WelcomeEmailData(
        email=email,
        user_name=user_name,
    )
    await notification_use_case.send_welcome_email(welcome_data)


@async_shared_broker.task(retry_on_error=True)
async def send_password_reset_email(
    email_data: PasswordResetEmailData,
    context: Annotated[Context, TaskiqDepends()],
) -> None:
    """Send password reset email with token link. Failure allows user to retry."""
    notification_use_case = context.state.notification_use_case
    await notification_use_case.send_password_reset_email(email_data)


@async_shared_broker.task(retry_on_error=True)
async def send_password_changed_email(
    email: str,
    user_name: str,
    context: Annotated[Context, TaskiqDepends()],
) -> None:
    """Send password changed confirmation email."""
    notification_use_case = context.state.notification_use_case
    await notification_use_case.send_password_changed_email(email, user_name)


@async_shared_broker.task(retry_on_error=True)
async def send_email_verification(
    email_data: EmailVerificationData,
    context: Annotated[Context, TaskiqDepends()],
) -> None:
    """Send email verification email with token link."""
    notification_use_case = context.state.notification_use_case
    await notification_use_case.send_email_verification(email_data)
