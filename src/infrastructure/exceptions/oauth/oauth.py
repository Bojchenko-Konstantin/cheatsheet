from src.infrastructure.exceptions.oauth.base import OAuthException


class OAuthAccountCreationError(OAuthException):
    """Raised when an attempt to create an OAuth account to the database fails."""


class OAuthServiceLinkageError(OAuthException):
    """Raised when new OAuth service to account linkage fails"""


class UnlinkLastOAuthAccountError(OAuthException):
    """Raised when user tries to unlink the only existing account"""
