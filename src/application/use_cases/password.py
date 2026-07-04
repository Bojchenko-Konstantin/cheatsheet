from typing import Any
from uuid import UUID

from src.application.interfaces import (
    IPasswordResetService,
    ITokenService,
    IUserService,
)


class PasswordUseCase:
    """Use case for password management operations."""

    def __init__(
        self,
        user_service: IUserService,
        password_reset_service: IPasswordResetService,
        token_service: ITokenService,
    ):
        self._user_service = user_service
        self._password_reset_service = password_reset_service
        self._token_service = token_service

    async def request_password_reset(self, email: str) -> dict[str, Any] | None:
        """Handle password reset request and generate reset token."""
        user = await self._user_service.get_password_reset_data(email)

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
        """Verify reset token and update password."""
        payload = self._password_reset_service.verify_reset_token(token)
        await self._user_service.reset_password(payload.user_id, new_password)
        await self._token_service.revoke_all_user_tokens(payload.user_id)
        user = await self._user_service.get_by_id(payload.user_id)

        return {
            "user_id": str(payload.user_id),
            "user_name": user.user_name,
            "email": payload.email,
        }

    async def update_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        """Change password for authenticated user."""
        await self._user_service.update_password(user_id, old_password, new_password)
