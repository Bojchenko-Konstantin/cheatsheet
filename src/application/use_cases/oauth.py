from uuid import UUID

from src.application.dto.auth import UserPayload
from src.application.dto.oauth import OAuthService
from src.application.interfaces import (
    IOAuthAccountService,
    IOAuthProviderService,
    ITokenService,
)


class OAuthUseCase:
    def __init__(
        self,
        token_service: ITokenService,
        oauth_account_service: IOAuthAccountService,
        oauth_provider_service: IOAuthProviderService,
    ):
        self._token_service = token_service
        self._oauth_account_service = oauth_account_service
        self._oauth_provider_service = oauth_provider_service

    async def authenticate(
        self, code: str, oauth_service: OAuthService
    ) -> dict[str, str]:
        """Executes the full OAuth authentication flow for a user."""
        access_token = await self._oauth_provider_service.get_access_token(code)
        user_info = await self._oauth_provider_service.get_user_info(access_token)

        user_id = await self._oauth_account_service.process_oauth_login(
            user_info, oauth_service
        )
        payload = UserPayload.create(user_id=user_id)
        token_pair = await self._token_service.generate_tokens(payload)

        return token_pair

    async def unlink_account(self, user_id: UUID, oauth_service: OAuthService):
        await self._oauth_account_service.unlink_oauth_account(user_id, oauth_service)
