from src.application.dto import EmailMessage, EmailType, WelcomeEmailData
from src.application.email_templates.welcome import (
    WELCOME_EMAIL_SUBJECT,
    WELCOME_EMAIL_TEMPLATE,
)
from src.application.interfaces.email_template_service import IEmailTemplateService
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
