from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.exception_handlers import email_not_verified_handler
from src.api.middleware import UnhandledExceptionMiddleware
from src.api.v1.routers.auth import router as router_auth
from src.api.v1.routers.cheatsheet import router as router_cheatsheet
from src.api.v1.routers.oauth import router_oauth_yandex
from src.application.exceptions.user import UserNotVerifiedError
from src.core.logging_config import setup_logging
from src.infrastructure.background_tasks.broker import BROKER
from src.infrastructure.database import dispose
from src.infrastructure.services.oauth.yandex import YandexOAuthService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    setup_logging()
    yandex_oauth_service = YandexOAuthService()
    app.state.yandex_oauth_service = yandex_oauth_service

    if not BROKER.is_worker_process:
        await BROKER.startup()
    yield
    if not BROKER.is_worker_process:
        await BROKER.shutdown()

    await dispose()
    await yandex_oauth_service.aclose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(UnhandledExceptionMiddleware)
app.add_exception_handler(UserNotVerifiedError, email_not_verified_handler)  # type: ignore[arg-type]

app.include_router(router_cheatsheet)
app.include_router(router_auth)
app.include_router(router_oauth_yandex)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
    )
