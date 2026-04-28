import base64
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
    PublicKeyTypes,
)


class JWTCoreService:
    """Low-level JWT operations: encode, decode, key loading."""

    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str,
    ):
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm

    def generate_token(
        self,
        payload: dict[str, Any],
        token_type: str,
        expires_in_minutes: int,
    ) -> str:
        now = datetime.now(tz=timezone.utc)
        expiration_time = now + timedelta(minutes=expires_in_minutes)

        full_payload = {
            "type": token_type,
            "exp": expiration_time,
            **payload,
        }

        private_key = self._get_appropriate_private_key_form()

        try:
            token = jwt.encode(
                payload=full_payload,
                key=private_key,  # type: ignore
                algorithm=self._algorithm,
            )
        except jwt.PyJWTError:
            raise
        except Exception as e:
            raise jwt.PyJWTError from e

        return token

    def verify_token(
        self,
        token: str,
        expected_type: str,
        required_claims: list[str],
    ) -> dict[str, Any]:
        """Verify and decode a JWT token."""
        public_key = self._get_appropriate_public_key_form()

        try:
            payload = jwt.decode(
                jwt=token,
                key=public_key,  # type: ignore
                algorithms=[self._algorithm],
                options={"require": required_claims},
            )
        except jwt.ExpiredSignatureError:
            raise
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            raise jwt.InvalidTokenError from e

        if payload.get("type") != expected_type:
            raise jwt.InvalidTokenError

        return payload

    def _get_appropriate_private_key_form(self) -> PrivateKeyTypes:
        """Load and return private key from base64 encoded DER string."""
        private_key_der = base64.b64decode(self._private_key)
        private_key = serialization.load_der_private_key(private_key_der, password=None)
        return private_key

    def _get_appropriate_public_key_form(self) -> PublicKeyTypes:
        """Load and return public key from base64 encoded DER string."""
        public_key_der = base64.b64decode(self._public_key)
        public_key = serialization.load_der_public_key(public_key_der)
        return public_key
