import base64
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
    PublicKeyTypes,
)

from src.application.dto import PasswordResetTokenPayload
from src.application.exceptions import (
    PasswordResetTokenExpiredError,
    PasswordResetTokenInvalidError,
)
from src.application.interfaces.services.password_reset_service import (
    IPasswordResetService,
)


class PasswordResetService(IPasswordResetService):
    """Stateless implementation of password reset service using JWT tokens."""

    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str,
        token_expires_in_minutes: int,
        frontend_reset_url: str,
    ):
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm
        self._token_expires_in_minutes = token_expires_in_minutes
        self._frontend_reset_url = frontend_reset_url.rstrip("/")

    def generate_reset_token(self, user_id: UUID, email: str) -> str:
        now = datetime.now(tz=timezone.utc)
        expiration_time = now + timedelta(minutes=self._token_expires_in_minutes)

        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "password_reset",  # Prevent access token use for password reset
            "exp": expiration_time,
        }

        private_key = self._get_appropriate_private_key_form()

        try:
            token = jwt.encode(
                payload=payload,
                key=private_key,  # type: ignore
                algorithm=self._algorithm,
            )
        except jwt.PyJWTError as e:
            raise PasswordResetTokenInvalidError from e
        except Exception as e:
            raise PasswordResetTokenInvalidError from e

        return token

    def verify_reset_token(self, token: str) -> PasswordResetTokenPayload:
        public_key = self._get_appropriate_public_key_form()

        try:
            payload = jwt.decode(
                jwt=token,
                key=public_key,  # type: ignore
                algorithms=[self._algorithm],
                options={"require": ["exp", "sub", "email", "type"]},
            )
        except jwt.ExpiredSignatureError as e:
            raise PasswordResetTokenExpiredError from e
        except jwt.InvalidTokenError as e:
            raise PasswordResetTokenInvalidError from e
        except Exception as e:
            raise PasswordResetTokenInvalidError from e

        if payload.get("type") != "password_reset":
            raise PasswordResetTokenInvalidError

        try:
            user_id = UUID(payload["sub"])
        except (ValueError, KeyError) as e:
            raise PasswordResetTokenInvalidError from e

        return PasswordResetTokenPayload(
            user_id=user_id,
            email=payload["email"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )

    def get_reset_url(self, token: str) -> str:
        return f"{self._frontend_reset_url}?token={token}"

    def _get_appropriate_private_key_form(self) -> PrivateKeyTypes:
        private_key_der = base64.b64decode(self._private_key)
        private_key = serialization.load_der_private_key(private_key_der, password=None)
        return private_key

    def _get_appropriate_public_key_form(self) -> PublicKeyTypes:
        public_key_der = base64.b64decode(self._public_key)
        public_key = serialization.load_der_public_key(public_key_der)
        return public_key
