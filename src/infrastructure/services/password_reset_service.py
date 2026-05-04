from datetime import datetime, timezone
from uuid import UUID

import jwt

from src.application.dto import PasswordResetTokenPayload
from src.application.exceptions import (
    ExpiredPasswordResetTokenError,
    InvalidPasswordResetTokenError,
)
from src.application.interfaces.services import IPasswordResetService
from src.infrastructure.services.jwt_core_service import JWTCoreService


class PasswordResetService(IPasswordResetService):
    """Stateless implementation of password reset service using JWT tokens."""

    _TOKEN_TYPE = "password_reset"
    _REQUIRED_CLAIMS = ["exp", "sub", "email", "type"]

    def __init__(
        self,
        jwt_core: JWTCoreService,
        frontend_reset_url: str,
        token_expires_in_minutes: int,
    ):
        self._jwt_core = jwt_core
        self._token_expires_in_minutes = token_expires_in_minutes
        self._frontend_reset_url = frontend_reset_url.rstrip("/")

    def generate_reset_token(self, user_id: UUID, email: str) -> str:
        """Generate a stateless JWT token for password reset."""
        payload = {
            "sub": str(user_id),
            "email": email,
        }

        try:
            return self._jwt_core.generate_token(
                payload=payload,
                token_type=self._TOKEN_TYPE,
                expires_in_minutes=self._token_expires_in_minutes,
            )
        except jwt.PyJWTError as e:
            raise InvalidPasswordResetTokenError from e

    def verify_reset_token(self, token: str) -> PasswordResetTokenPayload:
        """Verify and decode a password reset token."""
        try:
            payload = self._jwt_core.verify_token(
                token=token,
                expected_type=self._TOKEN_TYPE,
                required_claims=self._REQUIRED_CLAIMS,
            )
        except jwt.ExpiredSignatureError as e:
            raise ExpiredPasswordResetTokenError from e
        except jwt.InvalidTokenError as e:
            raise InvalidPasswordResetTokenError from e

        user_id = UUID(payload["sub"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        return PasswordResetTokenPayload(
            user_id=user_id,
            email=payload["email"],
            exp=exp,
        )

    def get_reset_url(self, token: str) -> str:
        """Build the full password reset URL with token."""
        return f"{self._frontend_reset_url}?token={token}"
