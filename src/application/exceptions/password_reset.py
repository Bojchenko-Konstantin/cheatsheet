from src.application.exceptions.base import ApplicationException


class PasswordResetException(ApplicationException):
    """Base exception for password reset errors."""


class InvalidPasswordResetTokenError(PasswordResetException):
    """Raised when password reset token is invalid or malformed."""


class ExpiredPasswordResetTokenError(PasswordResetException):
    """Raised when password reset token has expired."""
