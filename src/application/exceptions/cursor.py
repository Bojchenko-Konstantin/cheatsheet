from src.application.exceptions.base import ApplicationException


class CursorException(ApplicationException):
    """Base exception for based-cursor pagination."""


class InvalidCursorError(CursorException):
    """Raised when cursor is malformed or expired."""
