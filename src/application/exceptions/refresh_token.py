from src.application.exceptions.base import ApplicationException


class RefreshTokenException(ApplicationException):
    """Base exception class for refresh token-related errors."""


class RefreshTokenNotFoundError(RefreshTokenException):
    """Raised when refresh token is not found."""


class RefreshTokenBlacklistAddError(RefreshTokenException):
    """Raised when refresh token is not move to blacklist."""


class RefreshTokenCompromisedMarkError(RefreshTokenException):
    """Raised when refresh token fails to be marked as compromised."""


class RefreshTokenRevokeError(RefreshTokenException):
    """Raised when refresh token revocation fails."""


class RefreshTokenCompromisedError(RefreshTokenException):
    """Raised when refresh token is proven to be compromised."""
