from src.application.exceptions.base import ApplicationException


class CheatsheetException(ApplicationException):
    """Base exception for cheatsheet infrastructure errors."""


class CheatsheetNotFoundError(CheatsheetException):
    """Raised when a cheatsheet is not found in storage."""


class CheatsheetCreationError(CheatsheetException):
    """Raised when persisting a new cheatsheet fails."""


class CheatsheetUpdateError(CheatsheetException):
    """Raised when persisting an update fails."""


class CheatsheetListError(CheatsheetException):
    """Raised when cheatsheet list query fails."""


class CheatsheetSuggestionsError(CheatsheetException):
    """Raised when suggestions query fails."""
