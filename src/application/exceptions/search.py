from src.application.exceptions.base import ApplicationException


class SearchException(ApplicationException):
    """Base exception for search-related errors."""


class InvalidSearchQueryError(SearchException):
    """Raised when search query does not meet minimum length requirements."""


class InvalidSortFieldError(SearchException):
    """Raised when sort field is not in allowed set."""


class InvalidSortOrderError(SearchException):
    """Raised when sort order is not 'asc' or 'desc'."""
