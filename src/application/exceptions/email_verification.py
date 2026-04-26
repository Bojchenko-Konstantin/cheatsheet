from src.application.exceptions.base import ApplicationException


class EmailVerificationException(ApplicationException):
    """Base exception for email verification errors."""


class EmailVerificationTokenInvalidError(EmailVerificationException):
    """Raised when email verification token is invalid."""


class EmailVerificationTokenExpiredError(EmailVerificationException):
    """Raised when email verification token has expired."""


class EmailAlreadyVerifiedError(EmailVerificationException):
    """Raised when trying to verify an already verified email."""
