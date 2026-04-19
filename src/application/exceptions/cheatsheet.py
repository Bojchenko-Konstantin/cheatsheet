from src.application.exceptions.base import ApplicationException


class CheatsheetException(ApplicationException):
    """Base exception class for cheatsheet-related errors."""


class CheatsheetNotFoundError(CheatsheetException):
    """Raised when cheatsheet is not found by its ID."""


class CheatsheetCreationError(CheatsheetException):
    """Raised when cheatsheet creation fails."""


class CheatsheetUpdateError(CheatsheetException):
    """Raised when cheatsheet update fails."""


class CheatsheetAccessDeniedError(CheatsheetException):
    """Raised when user does not have permission to access a cheatsheet."""
