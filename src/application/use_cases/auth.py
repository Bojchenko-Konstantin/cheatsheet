from typing import Any
from uuid import UUID

from src.application.dto import User, UserPayload
from src.application.interfaces import (
    IEmailTemplateService,
    INotificationService,
    IPasswordResetService,
    ITokenService,
    IUserService,
)


class AuthUseCase:
    def __init__(
        self,
        token_service: ITokenService,
        user_service: IUserService,
        token_expires_in_minutes: int,
        notification_service: INotificationService | None = None,
        template_service: IEmailTemplateService | None = None,
        password_reset_service: IPasswordResetService | None = None,
    ):
        self._token_service = token_service
        self._user_service = user_service
        self._notification_service = notification_service
        self._template_service = template_service
        self._password_reset_service = password_reset_service
        self._token_expires_in_minutes = token_expires_in_minutes

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

    async def request_password_reset(self, email: str) -> dict[str, Any] | None:
        if not self._password_reset_service:
            return None

        user = await self._user_service.get_by_email(email)

        if user is not None:
            token = self._password_reset_service.generate_reset_token(
                user.user_id, email
            )
            reset_url = self._password_reset_service.get_reset_url(token)

            return {
                "email": email,
                "user_name": user.user_name,
                "reset_url": reset_url,
            }

        return None

    async def confirm_password_reset(
        self, token: str, new_password: str
    ) -> dict[str, Any]:
        if not self._password_reset_service:
            raise RuntimeError("Password reset service not configured")

        payload = self._password_reset_service.verify_reset_token(token)

        await self._user_service.update_password(payload.user_id, new_password)

        await self._token_service.revoke_all_user_tokens(payload.user_id)

        user = await self._user_service.get_by_id(payload.user_id)

        return {
            "user_id": str(payload.user_id),
            "user_name": user.user_name,
            "email": payload.email,
        }
