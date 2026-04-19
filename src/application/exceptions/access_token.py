from src.application.exceptions.base import ApplicationException


class AccessTokenException(ApplicationException):
    """Base exception class for access token-related errors."""


class AccessTokenGenerationError(AccessTokenException):
    """Raised when access token generation fails."""


class AccessTokenExpiredError(AccessTokenException):
    """Raised when access token has expired."""
