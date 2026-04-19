from src.application.exceptions.base import ApplicationException


class NotificationException(ApplicationException):
    """Base exception class for notification error."""


class SendEmailError(NotificationException):
    """Raised when email sending fails."""
