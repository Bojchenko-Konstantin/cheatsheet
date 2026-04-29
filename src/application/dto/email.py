from dataclasses import dataclass
from enum import StrEnum


class EmailType(StrEnum):
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_VERIFICATION = "email_verification"


@dataclass(slots=True)
class EmailMessage:
    """Email ready for sending via notification service."""

    to: str
    subject: str
    text: str
    email_type: EmailType

    def to_api_payload(self) -> dict[str, str]:
        return {
            "to": self.to,
            "subject": self.subject,
            "text": self.text,
        }


@dataclass(slots=True)
class WelcomeEmailData:
    """Data for welcome email template."""

    email: str
    user_name: str
    first_name: str | None = None

    def get_display_name(self) -> str:
        return self.user_name


@dataclass(slots=True)
class PasswordResetEmailData:
    """Data for password reset email with token link."""

    email: str
    user_name: str
    reset_url: str
    first_name: str | None = None

    def get_display_name(self) -> str:
        return self.user_name


@dataclass(slots=True)
class EmailVerificationData:
    """Data for email verification email template."""

    email: str
    user_name: str
    verification_url: str
    first_name: str | None = None

    def get_display_name(self) -> str:
        return self.user_name
