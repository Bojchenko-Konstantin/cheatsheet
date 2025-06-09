import logging
from collections.abc import Callable
from logging.config import dictConfig

from core.config import settings


def filter_maker(level: str) -> Callable:
    level_priority = getattr(logging, level)

    def filter(record: logging.LogRecord):
        return record.levelno < level_priority

    return filter


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "()": "uvicorn.logging.ColourizedFormatter",
            "fmt": "%(levelprefix)s %(asctime)s %(message)s",
        },
        "verbose": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": (
                "%(levelprefix)s %(name)s %(asctime)s %(module)s "
                "%(process)d %(thread)d %(message)s"
            ),
        },
        "sql": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(name)s %(asctime)s %(module)s %(message)s",
        },
    },
    "filters": {
        "level_filter": {
            "()": f"{__name__}.filter_maker",
            "level": "WARNING",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG",
        },
        "sql_console": {
            "class": "logging.StreamHandler",
            "formatter": "sql",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": ["sql_console"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
    },
}


def setup_logging():
    dictConfig(LOGGING)
