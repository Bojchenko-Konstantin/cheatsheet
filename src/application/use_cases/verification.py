from typing import Any
from uuid import UUID

from src.application.exceptions import EmailAlreadyVerifiedError
from src.application.interfaces import (
    IUserService,
    IVerificationService,
)


class VerificationUseCase:
    """Use case for email verification operations."""

    def __init__(
        self,
        user_service: IUserService,
        email_verification_service: IVerificationService,
    ):
        self._user_service = user_service
        self._email_verification_service = email_verification_service

    async def request_email_verification(self, user_id: UUID) -> dict[str, Any]:
        """Generate email verification token and prepare verification data."""
        user = await self._user_service.get_by_id(user_id)

        if user.is_verified:
            raise EmailAlreadyVerifiedError

        email = await self._user_service.get_email_by_id(user_id)

        token = self._email_verification_service.generate_verification_token(
            user.user_id, email
        )
        verification_url = self._email_verification_service.get_verification_url(token)

        return {
            "email": email,
            "user_name": user.user_name,
            "verification_url": verification_url,
            "user_id": str(user.user_id),
        }

    async def confirm_email_verification(self, token: str) -> dict[str, Any]:
        """Verify email using verification token."""
        payload = self._email_verification_service.verify_token(token)

        user = await self._user_service.get_by_id(payload.user_id)

        if user.is_verified:
            raise EmailAlreadyVerifiedError

        await self._user_service.verify_email(payload.user_id)

        return {
            "user_id": str(payload.user_id),
            "email": payload.email,
            "user_name": user.user_name,
        }
