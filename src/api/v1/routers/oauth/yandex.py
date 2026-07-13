import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from src.api.dependencies import (
    CurrentUserRequiredDep,
    YandexOAuthServiceDep,
    YandexOAuthUseCaseDep,
)
from src.api.schemas import OAuthCallbackParams
from src.application.dto import OAuthService
from src.application.exceptions import UnlinkLastOAuthAccountError
from src.core.config import settings
from src.infrastructure.exceptions import YandexOAuthException
from src.infrastructure.services.oauth import generate_pkce_pair, generate_state_value

router = APIRouter(tags=["Yandex OAuth"])

logger = logging.getLogger(__name__)


@router.get("/auth/yandex/login")
async def login(oauth_provider_service: YandexOAuthServiceDep):
    state = generate_state_value()
    code_verifier, code_challenge = generate_pkce_pair()

    url = oauth_provider_service.generate_authorization_request_url(
        state, code_challenge
    )
    response = RedirectResponse(url=url)
    cookie_params = {
        "max_age": 300,
        "httponly": True,
        "secure": settings.cookie.secure,
        "samesite": "lax",
        "path": "/",
    }

    response.set_cookie(key="yandex_oauth_state", value=state, **cookie_params)
    response.set_cookie(
        key="yandex_oauth_code_verifier", value=code_verifier, **cookie_params
    )

    return response


@router.get("/auth/yandex/callback")
async def callback(
    request: Request,
    oauth_use_case: YandexOAuthUseCaseDep,
    params: Annotated[OAuthCallbackParams, Query()],
):
    state_from_cookie = request.cookies.get("yandex_oauth_state")
    code_verifier_from_cookie = request.cookies.get("yandex_oauth_code_verifier")

    if state_from_cookie != params.state:
        raise HTTPException(status_code=400, detail="Invalid state — possible CSRF")

    if not code_verifier_from_cookie:
        raise HTTPException(status_code=400, detail="Missing PKCE code verifier")

    try:
        token_pair = await oauth_use_case.authenticate(
            code=params.code,
            code_verifier=code_verifier_from_cookie,
            oauth_service=OAuthService.YANDEX,
        )
    except YandexOAuthException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Yandex OAuth error: {str(e)}",
        ) from None

    response = RedirectResponse(url="/cheatsheet", status_code=303)
    cookie_params = {
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "max_age": 30,
        "path": "/",
    }
    response.set_cookie(
        key="access_token", value=token_pair.access_token, **cookie_params
    )
    response.set_cookie(
        key="refresh_token", value=token_pair.refresh_token, **cookie_params
    )

    response.delete_cookie("yandex_oauth_state", path="/")
    response.delete_cookie("yandex_oauth_code_verifier", path="/")

    return response


@router.delete("auth/yandex/connections")
async def unlink(
    current_user: CurrentUserRequiredDep,
    oauth_use_case: YandexOAuthUseCaseDep,
):
    user_id = current_user.user_id

    try:
        await oauth_use_case.unlink_account(user_id, OAuthService.YANDEX)
    except UnlinkLastOAuthAccountError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink the only login way",
        ) from None
