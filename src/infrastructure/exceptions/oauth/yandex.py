from src.infrastructure.exceptions.oauth.base import OAuthException


class YandexOAuthException(OAuthException):
    """Base exception class for Yandex OAuth-related errors."""


class YandexTokenRequestError(YandexOAuthException):
    """Raised when the token exchange request fails with a non‑200 HTTP status."""


class YandexTokenResponseParseError(YandexOAuthException):
    """Raised when the token response cannot be parsed as valid JSON."""


class YandexAccessTokenMissingError(YandexOAuthException):
    """Raised when the access token is missing from the token response."""


class YandexUserInfoRequestError(YandexOAuthException):
    """Raised when the user info request fails with a non‑200 HTTP status."""


class YandexUserInfoResponseParseError(YandexOAuthException):
    """Raised when the user info response cannot be parsed as valid JSON."""
