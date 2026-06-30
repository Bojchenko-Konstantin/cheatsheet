import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from src.api.dependencies import (
    CurrentUserRequiredDep,
    OAuthUseCaseDep,
    YandexOAuthServiceDep,
)
from src.api.schemas import OAuthCallbackParams
from src.application.dto.oauth import OAuthService
from src.infrastructure.exceptions.oauth.oauth import UnlinkLastOAuthAccountError

router = APIRouter(tags=["OAuth"])

logger = logging.getLogger(__name__)


@router.get("/auth/yandex/login")
async def login_with_yandex(oauth_provider_service: YandexOAuthServiceDep):
    state = oauth_provider_service.generate_state_value()
    url = oauth_provider_service.generate_authorization_request_url(state)
    response = RedirectResponse(url=url)

    response.set_cookie(
        key="yandex_oauth_state",
        value=state,
        max_age=300,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    return response


@router.get("/auth/yandex/callback")
async def yandex_auth_callback(
    request: Request,
    oauth_use_case: OAuthUseCaseDep,
    params: Annotated[OAuthCallbackParams, Query()],
):
    state_from_cookie = request.cookies.get("yandex_oauth_state")

    if state_from_cookie != params.state:
        raise HTTPException(status_code=400, detail="Invalid state — possible CSRF")

    token_pair = await oauth_use_case.authenticate(
        code=params.code, oauth_service=OAuthService.YANDEX
    )

    redirect_url = (
        f"/cheatsheet#access_token={token_pair['access_token']}"
        f"&refresh_token={token_pair['refresh_token']}"
    )

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.delete_cookie("yandex_oauth_state", path="/")

    return response


@router.delete("auth/yandex/connections")
async def unlink_yandex_account(
    current_user: CurrentUserRequiredDep,
    oauth_use_case: OAuthUseCaseDep,
):
    user_id = current_user.user_id

    try:
        await oauth_use_case.unlink_account(user_id, OAuthService.YANDEX)
    except UnlinkLastOAuthAccountError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink the only login way",
        ) from None
    # Add possible logout.
