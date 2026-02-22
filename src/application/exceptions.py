class ApplicationException(Exception):
    """This the base exception class for application layer."""


class CheatsheetException(ApplicationException):
    """This the base exception class for cheatsheet."""


class RefreshTokenException(ApplicationException):
    """This the base exception class for refresh token."""


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


class RefreshTokenNotFoundError(RefreshTokenException):
    """This exception will raise when refresh token was not found."""


class RefreshTokenMoveToBlacklistError(RefreshTokenException):
    """This exception will raise when refresh token was not move to blacklist."""


class RefreshTokenMarkAsCompromisedError(RefreshTokenException):
    """
    This exception will raise when refresh token fails
    to be marked as compromised.
    """


class UserNotFoundError(UserException):
    """This exception will raise when user was not found."""


class UserCreationError(UserException):
    """This exception will raise when user failed to be created."""
