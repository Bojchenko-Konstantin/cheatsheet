from httpx import AsyncClient, Limits, Timeout

from src.core.config import settings

headers = {
    "User-Agent": (
        f"{settings.app_credentials.name} (Contact: {settings.app_credentials.email})"
    )
}
limits = Limits(max_keepalive_connections=10, max_connections=50, keepalive_expiry=10.0)
timeout = Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)

ASYNC_CLIENT = AsyncClient(timeout=timeout, limits=limits, headers=headers)
