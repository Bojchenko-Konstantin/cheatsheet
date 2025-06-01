import logging
from collections.abc import Callable
from logging.config import dictConfig

from config import BASE_DIR, settings

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


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
            "use_colors": False,
        },
        "sql": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(name)s %(asctime)s %(module)s\n%(message)s",
            "use_colors": False,
        },
    },
    "filters": {
        "level_filter": {
            "()": f"{__name__}.filter_maker",
            "level": "WARNING",
        }
    },
    "handlers": {
        "app_debug": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": LOG_DIR / "app_debug.log",
            "filters": ["level_filter"],
            "level": "DEBUG",
        },
        "app_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": LOG_DIR / "app_error.log",
            "level": "WARNING",
        },
        "sql_debug": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "maxBytes": 10**7,
            "formatter": "sql",
            "filename": LOG_DIR / "sql_debug.log",
            "filters": ["level_filter"],
            "level": "DEBUG",
        },
        "sql_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": LOG_DIR / "sql_error.log",
            "level": "WARNING",
        },
        "uvicorn_debug": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 10,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": LOG_DIR / "uvicorn_debug.log",
            "filters": ["level_filter"],
            "level": "DEBUG",
        },
        "uvicorn_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 10,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": LOG_DIR / "uvicorn_error.log",
            "level": "WARNING",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "app_debug", "app_error"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "uvicorn_debug", "uvicorn_error"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "alembic": {
            "handlers": ["sql_debug", "sql_error"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": ["sql_debug", "sql_error"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
    },
}


def setup_logging():
    dictConfig(LOGGING)
