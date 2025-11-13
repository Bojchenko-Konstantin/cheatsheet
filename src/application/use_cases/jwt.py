import base64
from datetime import datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from pwdlib import PasswordHash
from uuid_extensions import uuid7


class JWTUseCase:
    """
    Handles all operations with JWT tokens.
    """

    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str,
        access_token_expires_in: int,
        refresh_token_expires_in: int,
    ):
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm
        self._access_token_expires_in = access_token_expires_in
        self._refresh_token_expires_in = refresh_token_expires_in

    async def get_jwt_tokens(self, payload: dict[str, Any]) -> dict[str, str]:
        access_token = self._get_access_token(payload)
        refresh_token = str(uuid7())
        password_hash = PasswordHash.recommended()

        # TODO This hash has to be saved in the database
        # with status (is_active) and device id.
        refresh_token_hash = password_hash.hash(refresh_token)  # noqa: F841

        return dict(access_token=access_token, refresh_token=refresh_token)

    def _get_access_token(self, payload: dict[str, Any]) -> str:
        expiration_time = datetime.now() + timedelta(
            minutes=self._access_token_expires_in
        )
        user_payload = payload.copy()
        user_payload["exp"] = expiration_time

        private_key = self._get_appropriate_private_key_form()
        access_token = jwt.encode(
            user_payload,
            private_key,  # type: ignore
            algorithm=self._algorithm,
        )
        return access_token

    def _get_appropriate_private_key_form(self) -> PrivateKeyTypes:
        private_key_der = base64.b64decode(self._private_key)
        private_key = serialization.load_der_private_key(private_key_der, password=None)
        return private_key
