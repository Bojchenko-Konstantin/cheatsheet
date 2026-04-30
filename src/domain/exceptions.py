class DomainException(Exception):
    """Base exception class for domain layer."""


class CheatsheetAccessDeniedError(DomainException):
    """Raised when a user attempts to access a private cheatsheet they don't own."""


class CheatsheetModificationDeniedError(DomainException):
    """Raised when a user attempts to modify a cheatsheet they don't own."""


class TagLimitExceededError(DomainException):
    """Raised when attempting to add more than the allowed number of tags."""


class InvalidCheatsheetTitleError(DomainException):
    """Raised when title does not meet length or content requirements."""


class InvalidCheatsheetContentError(DomainException):
    """Raised when content is empty or whitespace-only."""


class InvalidTagError(DomainException):
    """Raised when tag data fails validation."""


class NegativeStatsError(DomainException):
    """Raised when a stats operation would produce a negative value."""
