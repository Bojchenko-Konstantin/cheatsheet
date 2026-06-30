from src.application.exceptions.base import ApplicationException


class OAuthException(ApplicationException):
    """Base exception class for OAuth-related errors."""


class OAuthAccountCreationError(OAuthException):
    """Raised when OAuth account creation fails."""


class OAuthServiceLinkageError(OAuthException):
    """Raised when OAuth service linkage fails."""


class UnlinkLastOAuthAccountError(OAuthException):
    """Raised when user tries to unlink the only existing account."""
