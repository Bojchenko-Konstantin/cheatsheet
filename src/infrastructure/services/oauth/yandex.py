import logging
import secrets
from json import JSONDecodeError
from urllib.parse import urlencode

from httpx import AsyncClient, Timeout

from src.core.config import settings
from src.infrastructure.exceptions.oauth import (
    YandexAccessTokenMissingError,
    YandexRefreshTokenMissingError,
    YandexTokenRequestError,
    YandexTokenResponseParseError,
    YandexUserInfoRequestError,
    YandexUserInfoResponseParseError,
)

logger = logging.getLogger(__name__)


class YandexOAuthService:
    def __init__(self):
        # TODO: add additional settings
        # (retries, max connections, User-Agent header etc.)
        self._client = AsyncClient(timeout=Timeout(connect=5.0, timeout=10.0))

    def generate_authorization_request_url(self, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": settings.yandex_oauth.client_id,
            "redirect_uri": settings.yandex_oauth.callback_url,
            "scope": "login:email login:info",
            "state": state,
        }

        authorize_url = "https://oauth.yandex.ru/authorize"
        url = f"{authorize_url}?{urlencode(params)}"
        logger.debug("Generated Yandex authorization request URL: %s", url)
        return url

    def generate_state_value(self) -> str:
        return secrets.token_urlsafe(32)

    async def get_tokens(self, code: str) -> tuple[str, str]:
        request_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.yandex_oauth.client_id,
            "client_secret": settings.yandex_oauth.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        token_url = "https://oauth.yandex.ru/token"
        response = await self._client.post(
            url=token_url, data=request_data, headers=headers
        )

        if response.status_code != 200:
            logger.exception(
                "Failed to receive tokens: status_code=%s, body=%s",
                response.status_code,
                response.text,
            )
            raise YandexTokenRequestError

        try:
            response_data = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", token_url)
            raise YandexTokenResponseParseError from e

        access_token = response_data.get("access_token")
        refresh_token = response_data.get("refresh_token")

        if access_token is None:
            logger.error("access_token is not present: %s", response_data)
            raise YandexAccessTokenMissingError

        logger.info("Received access_token")

        if refresh_token is None:
            logger.exception("refresh_token is not present: %s", response_data)
            raise YandexRefreshTokenMissingError

        logger.info("Received refresh_token")

        return access_token, refresh_token

    async def refresh_a_token(self):
        pass

    async def get_user_info(self, access_token: str) -> dict[str, str]:
        headers = {"Authorization": f"OAuth {access_token}"}
        params = {"format": "json"}

        user_info_url = "https://login.yandex.ru/info"
        response = await self._client.get(
            url=user_info_url, headers=headers, params=params
        )

        if response.status_code != 200:
            logger.exception(
                "Failed to receive user_info: status_code=%s, body=%s",
                response.status_code,
                response.text,
            )
            raise YandexUserInfoRequestError

        try:
            user_info = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", user_info_url)
            raise YandexUserInfoResponseParseError from e

        logger.info("user_info was obtained successfully")
        return user_info
