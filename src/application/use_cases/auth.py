from typing import Any
from uuid import UUID

from src.application.dto import User, UserPayload
from src.application.interfaces import ITokenService, IUserService


class AuthUseCase:
    def __init__(self, token_service: ITokenService, user_service: IUserService):
        self._token_service = token_service
        self._user_service = user_service

    async def authenticate(self, user_name: str, password: str) -> dict[str, str]:
        user = await self._user_service.authenticate_user(user_name, password)
        payload = UserPayload.create(
            user_id=user.user_id, is_superuser=user.is_superuser
        )
        token_pair = await self._token_service.generate_tokens(payload)
        return token_pair

    async def register(self, create_data: dict[str, Any]) -> dict[str, str]:
        user = await self._user_service.create(create_data)
        payload = UserPayload.create(
            user_id=user.user_id, is_superuser=user.is_superuser
        )
        token_pair = await self._token_service.generate_tokens(payload)
        return token_pair

    async def refresh(self, refresh_data: dict[str, Any]) -> dict[str, str]:
        user_id = refresh_data["user_id"]

        await self._token_service.verify_refresh_token(
            user_id=user_id,
            plain_refresh_token=refresh_data["refresh_token"],
            fingerprint=refresh_data["fingerprint"],
        )
        user = await self._user_service.get_by_id(user_id)
        payload = UserPayload.create(
            user_id=user.user_id, is_superuser=user.is_superuser
        )
        token_pair = await self._token_service.generate_tokens(payload)
        return token_pair

    async def logout(self, user_id: UUID, refresh_token: str, fingerprint: str) -> None:
        await self._token_service.revoke_refresh_token(
            user_id=user_id,
            plain_refresh_token=refresh_token,
            fingerprint=fingerprint,
        )

    async def get_current_user(self, access_token: str) -> User:
        payload = await self._token_service.verify_access_token(access_token)
        user = await self._user_service.get_by_id(payload.user_id)
        return user
