class ApplicationException(Exception):
    """This the base exception class for application layer."""


class CheatsheetNotFoundError(ApplicationException):
    """This exception will raise when cheatsheet was not retrieved by ID."""
