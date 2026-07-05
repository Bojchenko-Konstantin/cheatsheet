from src.infrastructure.exceptions.oauth.base import ProviderServiceException


class GithubOAuthException(ProviderServiceException):
    """Base exception class for Github OAuth-related errors."""


class GithubTokenRequestError(GithubOAuthException):
    """Raised when the token exchange request fails with a non‑200 HTTP status."""


class GithubTokenResponseParseError(GithubOAuthException):
    """Raised when the token response cannot be parsed as valid JSON."""


class GithubAccessTokenMissingError(GithubOAuthException):
    """Raised when the access token is missing from the token response."""


class GithubUserInfoRequestError(GithubOAuthException):
    """Raised when the user info request fails with a non‑200 HTTP status."""


class GithubUserEmailRequestError(GithubOAuthException):
    """Raised when the user email request fails with a non‑200 HTTP status."""


class GithubUserEmailAbsentError(GithubOAuthException):
    """Raised when verified user email is absent."""


class GithubUserInfoResponseParseError(GithubOAuthException):
    """Raised when the user info response cannot be parsed as valid JSON."""


class GithubUserEmailResponseParseError(GithubOAuthException):
    """Raised when the user email response cannot be parsed as valid JSON."""


class GithubServerRequestError(GithubOAuthException):
    """Raised when Github server returns 5XX errors"""
