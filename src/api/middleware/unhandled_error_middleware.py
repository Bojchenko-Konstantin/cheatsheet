import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class UnhandledExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_unhandled_exception(request, request_id, exc)

    async def handle_unhandled_exception(
        self, request: Request, request_id: str, exc: Exception
    ) -> ORJSONResponse:
        logger.critical(
            "Unhandled exception occurred: %s - %s",
            exc.__class__.__name__,
            str(exc),
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            },
            exc_info=exc,
        )

        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )
