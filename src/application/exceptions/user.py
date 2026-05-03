from src.application.exceptions.base import ApplicationException


class UserException(ApplicationException):
    """Base exception class for user-related errors."""


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


class PasswordsDontMatchError(UserException):
    """Raised when password and confirmation password don't match."""
