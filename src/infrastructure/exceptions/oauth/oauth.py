from src.infrastructure.exceptions.oauth.base import OAuthException


class OAuthAccountCreationError(OAuthException):
    """Raised when an attempt to create an OAuth account to the database fails."""
