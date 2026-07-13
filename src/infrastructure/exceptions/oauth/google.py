from src.infrastructure.exceptions.oauth.base import ProviderServiceException


class GoogleOAuthException(ProviderServiceException):
    """Base exception class for Google OAuth-related errors."""


class GoogleTokenRequestError(GoogleOAuthException):
    """Raised when the token exchange request fails with a non‑200 HTTP status."""


class GoogleTokenResponseParseError(GoogleOAuthException):
    """Raised when the token response cannot be parsed as valid JSON."""


class GoogleAccessTokenMissingError(GoogleOAuthException):
    """Raised when the access token is missing from the token response."""


class GoogleUserInfoRequestError(GoogleOAuthException):
    """Raised when the user info request fails with a non‑200 HTTP status."""


class GoogleUserInfoResponseParseError(GoogleOAuthException):
    """Raised when the user info response cannot be parsed as valid JSON."""


class GoogleServerRequestError(GoogleOAuthException):
    """Raised when Google server returns 5xx errors"""
