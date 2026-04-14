class ApplicationException(Exception):
    """Base exception class for application layer."""


class CheatsheetException(ApplicationException):
    """Base exception class for cheatsheet-related errors."""


class RefreshTokenException(ApplicationException):
    """Base exception class for refresh token-related errors."""


class AccessTokenException(ApplicationException):
    """Base exception class for access token-related errors."""


class UserException(ApplicationException):
    """Base exception class for user-related errors."""


class CheatsheetNotFoundError(CheatsheetException):
    """Raised when cheatsheet is not found by its ID."""


class CheatsheetCreationError(CheatsheetException):
    """Raised when cheatsheet creation fails."""


class CheatsheetUpdateError(CheatsheetException):
    """Raised when cheatsheet update fails."""


class CheatsheetAccessDeniedError(CheatsheetException):
    """Raised when user does not have permission to access a cheatsheet."""


class AccessTokenGenerationError(AccessTokenException):
    """Raised when access token generation fails."""


class AccessTokenExpiredError(AccessTokenException):
    """Raised when access token has expired."""


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


class UserNotFoundError(UserException):
    """Raised when user is not found."""


class UserCreationError(UserException):
    """Raised when user creation fails."""


class DuplicateUserError(UserException):
    """Raised when user creation fails due to duplicate username."""


class UserInactiveError(UserException):
    """Raised when user is inactive."""


class UserAuthenticationError(UserException):
    """Raised when user authentication fails due to invalid credentials."""
