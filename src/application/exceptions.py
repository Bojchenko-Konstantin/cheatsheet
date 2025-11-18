class ApplicationException(Exception):
    """This the base exception class for application layer."""


class CheatsheetNotFoundError(ApplicationException):
    """This exception will raise when cheatsheet was not retrieved by ID."""


class CheatsheetCreationError(ApplicationException):
    """This exception will raise when cheatsheet failed to be created."""


class CheatsheetUpdateError(ApplicationException):
    """This exception will raise when cheatsheet failed to be updated."""
