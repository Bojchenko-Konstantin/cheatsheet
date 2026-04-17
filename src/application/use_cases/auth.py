from typing import Any
from uuid import UUID

from src.application.dto import User, UserPayload, WelcomeEmailData
from src.application.interfaces import ITokenService, IUserService
from src.application.use_cases.notification import NotificationUseCase


class AuthUseCase:
    def __init__(
        self,
        token_service: ITokenService,
        user_service: IUserService,
        notification_use_case: NotificationUseCase,
    ):
        self._token_service = token_service
        self._user_service = user_service
        self._notification_use_case = notification_use_case

    async def authenticate(self, user_name: str, password: str) -> dict[str, str]:
        user = await self._user_service.authenticate_user(user_name, password)
        payload = UserPayload.create(
            user_id=user.user_id, is_superuser=user.is_superuser
        )
        token_pair = await self._token_service.generate_tokens(payload)
        return token_pair

    async def register(self, create_data: dict[str, Any]) -> dict[str, str]:
        user_payload = await self._user_service.create(create_data)

        user = await self._user_service.get_by_id(user_payload.user_id)

        payload = UserPayload.create(
            user_id=user.user_id, is_superuser=user.is_superuser
        )
        token_pair = await self._token_service.generate_tokens(payload)

        email = create_data.get("email")
        if email:
            await self._send_welcome_email(
                email=email,
                username=user.user_name,
            )

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

    async def _send_welcome_email(self, email: str, username: str) -> None:
        """Send welcome email to new user. Failure doesn't affect registration."""
        if not email:
            return

        if not username:
            username = email.split("@")[0]

        welcome_data = WelcomeEmailData(
            email=email,
            user_name=username,
        )
        await self._notification_use_case.send_welcome_email(welcome_data)
