class ApplicationException(Exception):
    """This the base exception class for application layer."""


class CheatsheetException(ApplicationException):
    """This the base exception class for cheatsheet."""


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


class RefreshTokenNotFoundError(ApplicationException):
    """This exception will raise when refresh token was not found."""
