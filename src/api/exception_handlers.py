from fastapi import Request, status
from fastapi.responses import ORJSONResponse

from src.application.exceptions import UserNotVerifiedError


async def email_not_verified_handler(
    request: Request, exception: UserNotVerifiedError
) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": "Email not verified. "
            "Please verify your email to access this feature."
        },
    )
