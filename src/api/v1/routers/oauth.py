import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from src.api.dependencies import OAuthAccountServiceDep, YandexOAuthServiceDep
from src.api.schemas import OAuthCallbackParams

router = APIRouter(tags=["OAuth"])

logger = logging.getLogger(__name__)


@router.get("/auth/yandex/login")
async def login_with_yandex(oauth_service: YandexOAuthServiceDep):
    state = oauth_service.generate_state_value()
    url = oauth_service.generate_authorization_request_url(state)
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
    oauth_service: YandexOAuthServiceDep,
    oauth_account_service: OAuthAccountServiceDep,
    params: Annotated[OAuthCallbackParams, Query()],
):
    state_from_cookie = request.cookies.get("yandex_oauth_state")

    if state_from_cookie != params.state:
        raise HTTPException(status_code=400, detail="Invalid state — possible CSRF")

    access_token, refresh_token = await oauth_service.get_tokens(code=params.code)
    user_info = await oauth_service.get_user_info(access_token)
    response = RedirectResponse(url="/cheatsheet", status_code=303)
    response.delete_cookie("yandex_oauth_state", path="/")

    await oauth_account_service.save_account_with_refresh_token(
        refresh_token, user_info
    )
    # TODO:
    # create local refresh token to use in application
    # save user_info

    return response
