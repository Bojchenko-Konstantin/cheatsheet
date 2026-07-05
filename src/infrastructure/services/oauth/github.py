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
    GithubAccessTokenMissingError,
    GithubServerRequestError,
    GithubTokenRequestError,
    GithubTokenResponseParseError,
    GithubUserEmailAbsentError,
    GithubUserEmailRequestError,
    GithubUserEmailResponseParseError,
    GithubUserInfoRequestError,
    GithubUserInfoResponseParseError,
)

logger = logging.getLogger(__name__)


class GithubOAuthService(IOAuthProviderService):
    def __init__(self, async_client: AsyncClient):
        self._client = async_client
        self._client_id = settings.github_oauth.client_id
        self._callback_url = settings.github_oauth.callback_url
        self._client_secret = settings.github_oauth.client_secret

    def generate_authorization_request_url(
        self, state: str, code_challenge: str
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._callback_url,
            "scope": "read:user user:email",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        authorize_url = "https://github.com/login/oauth/authorize"
        url = f"{authorize_url}?{urlencode(params)}"
        logger.debug("Generated Github authorization request URL: %s", url)
        return url

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception_type((RequestError, GithubServerRequestError)),
    )
    async def get_access_token(self, code: str, code_verifier: str) -> str:
        request_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code_verifier": code_verifier,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        token_url = "https://github.com/login/oauth/access_token"
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
                raise GithubServerRequestError

            raise GithubTokenRequestError

        try:
            response_data = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", token_url)
            raise GithubTokenResponseParseError from e

        access_token = response_data.get("access_token")

        if access_token is None:
            logger.error("access_token is not present: %s", response_data)
            raise GithubAccessTokenMissingError

        logger.info("Received access_token")

        return access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception_type((RequestError, GithubServerRequestError)),
    )
    async def get_user_info(self, access_token: str) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        }
        user_info_url = "https://api.github.com/user"
        response = await self._client.get(url=user_info_url, headers=headers)

        if response.status_code != 200:
            logger.exception(
                "Failed to receive user_info: status_code=%s, body=%s",
                response.status_code,
                response.text,
            )

            if response.status_code >= 500:
                raise GithubServerRequestError

            raise GithubUserInfoRequestError

        try:
            user_info = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", user_info_url)
            raise GithubUserInfoResponseParseError from e

        user_info["email"] = await self._get_user_email(headers)

        logger.info("user_info was obtained successfully")
        return user_info

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        retry=retry_if_exception_type((RequestError, GithubServerRequestError)),
    )
    async def _get_user_email(self, headers: dict[str, str]) -> str | None:
        additional_email_url = "https://api.github.com/user/emails"
        response = await self._client.get(url=additional_email_url, headers=headers)

        if response.status_code != 200:
            logger.exception(
                "Failed to receive user_info: status_code=%s, body=%s",
                response.status_code,
                response.text,
            )

            if response.status_code >= 500:
                raise GithubServerRequestError

            raise GithubUserEmailRequestError

        try:
            user_emails = response.json()
        except JSONDecodeError as e:
            logger.exception("Failed to decode response from %s", additional_email_url)
            raise GithubUserEmailResponseParseError from e

        return self._find_appropriate_email(user_emails)

    @staticmethod
    def _find_appropriate_email(user_emails: list[dict[str, str]]) -> str:
        for email_params in user_emails:
            if email_params.get("primary") and email_params.get("verified"):
                return email_params["email"]

        for email_params in user_emails:
            if email_params.get("verified"):
                return email_params["email"]

        logger.exception("No verified email found for user")

        raise GithubUserEmailAbsentError
