class ApplicationException(Exception):
    """This the base exception class for application layer."""


class CheatsheetException(ApplicationException):
    """This the base exception class for cheatsheet."""


class RefreshTokenException(ApplicationException):
    """This the base exception class for refresh token."""


class AccessTokenException(ApplicationException):
    """This the base exception class for access token."""


class UserException(ApplicationException):
    """This the base exception class for user."""


class CheatsheetNotFoundError(CheatsheetException):
    """This exception will raise when cheatsheet was not retrieved by ID."""


class CheatsheetCreationError(CheatsheetException):
    """This exception will raise when cheatsheet failed to be created."""


class CheatsheetUpdateError(CheatsheetException):
    """This exception will raise when cheatsheet failed to be updated."""


class CheatsheetAccessDeniedError(CheatsheetException):
    """
    This exception will raise when user does not have permission
    to access a cheatsheet.
    """


class AccessTokenGenerationError(AccessTokenException):
    """This exception will raise when access token generation fails."""


class AccessTokenExpiredError(AccessTokenException):
    """This exception will raise when access token has expired."""


class RefreshTokenNotFoundError(RefreshTokenException):
    """This exception will raise when refresh token was not found."""


class RefreshTokenMoveToBlacklistError(RefreshTokenException):
    """This exception will raise when refresh token was not move to blacklist."""


class RefreshTokenMarkAsCompromisedError(RefreshTokenException):
    """
    This exception will raise when refresh token fails
    to be marked as compromised.
    """


class RefreshTokenWasCompromisedError(RefreshTokenException):
    """This exception will be raised when refresh token is proven to be compromised."""


class UserNotFoundError(UserException):
    """This exception will raise when user was not found."""


class UserCreationError(UserException):
    """This exception will raise when user failed to be created."""


class DuplicateUserError(UserException):
    """This exception will raise when user creation fails due to duplicate username."""


class UserInactiveError(UserException):
    """This exception will raise when user is inactive."""


class UserAuthenticationError(UserException):
    """
    This exception will raise when user authentication
    fails due to invalid credentials.
    """
