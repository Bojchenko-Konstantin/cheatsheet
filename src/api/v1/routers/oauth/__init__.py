__all__ = (
    "router_oauth_yandex",
    "router_oauth_github",
)

from .github import router as router_oauth_github
from .yandex import router as router_oauth_yandex
