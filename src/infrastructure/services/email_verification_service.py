from datetime import datetime, timezone
from uuid import UUID

import jwt

from src.application.dto import EmailVerificationTokenPayload
from src.application.exceptions import (
    ExpiredEmailVerificationTokenError,
    InvalidEmailVerificationTokenError,
)
from src.application.interfaces import IVerificationService
from src.infrastructure.services.jwt_core_service import JWTCoreService


class EmailVerificationService(IVerificationService):
    """Stateless implementation of email verification service using JWT tokens."""

    _TOKEN_TYPE = "email_verification"
    _REQUIRED_CLAIMS = ["exp", "sub", "email", "type"]

    def __init__(
        self,
        jwt_core: JWTCoreService,
        token_expires_in_hours: int,
        frontend_verify_url: str = "http://localhost:3000/verify-email",
    ):
        self._jwt_core = jwt_core
        self._token_expires_in_hours = token_expires_in_hours
        self._frontend_verify_url = frontend_verify_url.rstrip("/")

    def generate_verification_token(self, user_id: UUID, email: str) -> str:
        """Generate a stateless JWT token for email verification."""
        payload = {
            "sub": str(user_id),
            "email": email,
        }

        try:
            token = self._jwt_core.generate_token(
                payload=payload,
                token_type=self._TOKEN_TYPE,
                expires_in_minutes=self._token_expires_in_hours * 60,
            )
        except Exception as e:
            raise InvalidEmailVerificationTokenError from e

        return token

    def verify_token(self, token: str) -> EmailVerificationTokenPayload:
        """Verify and decode an email verification token."""
        try:
            payload = self._jwt_core.verify_token(
                token=token,
                expected_type=self._TOKEN_TYPE,
                required_claims=self._REQUIRED_CLAIMS,
            )
        except jwt.ExpiredSignatureError as e:
            raise ExpiredEmailVerificationTokenError from e
        except Exception as e:
            raise InvalidEmailVerificationTokenError from e

        try:
            user_id = UUID(payload["sub"])
        except (ValueError, KeyError) as e:
            raise InvalidEmailVerificationTokenError from e

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        return EmailVerificationTokenPayload(
            user_id=user_id,
            email=payload["email"],
            exp=exp,
        )

    def get_verification_url(self, token: str) -> str:
        """Build the full verification URL with token."""
        return f"{self._frontend_verify_url}?token={token}"
