from logging.config import dictConfig

from src.core.config import settings

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
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
        "sqlalchemy": {
            "handlers": ["sql_console"],
            "level": settings.logging.log_level,
            "propagate": False,
        },
    },
}


def setup_logging():
    dictConfig(LOGGING)
