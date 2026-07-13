__all__ = (
    "router_oauth_github",
    "router_oauth_google",
    "router_oauth_yandex",
)

from .github import router as router_oauth_github
from .google import router as router_oauth_google
from .yandex import router as router_oauth_yandex
