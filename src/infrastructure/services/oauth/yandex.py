import logging
from json import JSONDecodeError
from urllib.parse import urlencode

from httpx import AsyncClient, RequestError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.application.interfaces import IOAuthProviderService
from src.core.config import settings
from src.infrastructure.exceptions.oauth import (
    YandexAccessTokenMissingError,
    YandexServerRequestError,
    YandexTokenRequestError,
    YandexTokenResponseParseError,
    YandexUserInfoRequestError,
    YandexUserInfoResponseParseError,
)

logger = logging.getLogger(__name__)


class YandexOAuthService(IOAuthProviderService):
    def __init__(self, async_client: AsyncClient):
        self._client = async_client
        self._client_id = settings.yandex_oauth.client_id
        self._callback_url = settings.yandex_oauth.callback_url
        self._client_secret = settings.yandex_oauth.client_secret

    def generate_authorization_request_url(
        self, state: str, code_challenge: str
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._callback_url,
            "scope": "login:email login:info",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        authorize_url = "https://oauth.yandex.ru/authorize"
        url = f"{authorize_url}?{urlencode(params)}"
        logger.debug("Generated Yandex authorization request URL: %s", url)
        return url

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception_type((RequestError, YandexServerRequestError)),
    )
    async def get_access_token(self, code: str, code_verifier: str) -> str:
        request_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code_verifier": code_verifier,
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

            if response.status_code >= 500:
                logger.exception(
                    "Failed to receive tokens: status_code=%s, body=%s",
                    response.status_code,
                    response.text,
                )

                raise YandexServerRequestError

            raise YandexTokenRequestError

        try:
            response_data = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", token_url)
            raise YandexTokenResponseParseError from e

        access_token = response_data.get("access_token")

        if access_token is None:
            logger.error("access_token is not present: %s", response_data)
            raise YandexAccessTokenMissingError

        logger.info("Received access_token")

        return access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception_type((RequestError, YandexServerRequestError)),
    )
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

            if response.status_code >= 500:
                logger.exception(
                    "Failed to receive user_info: status_code=%s, body=%s",
                    response.status_code,
                    response.text,
                )
                raise YandexServerRequestError

            raise YandexUserInfoRequestError

        try:
            user_info = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", user_info_url)
            raise YandexUserInfoResponseParseError from e

        logger.info("user_info was obtained successfully")
        return user_info
