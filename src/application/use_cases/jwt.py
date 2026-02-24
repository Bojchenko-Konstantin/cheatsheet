import base64
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
    PublicKeyTypes,
)
from pwdlib import PasswordHash
from uuid_extensions import uuid7

from src.application.dto import RefreshToken, TokenStatus, UserPayload
from src.application.exceptions import AccessTokenGenerationError
from src.application.hasher import HASHER
from src.application.interfaces.unit_of_work import IUnitOfWork


class JWTUseCase:
    """
    Handles all operations with JWT tokens.
    """

    def __init__(
        self,
        unit_of_work: IUnitOfWork,
        private_key: str,
        public_key: str,
        algorithm: str,
        access_token_expires_in: int,
        refresh_token_expires_in: int,
        hasher: PasswordHash = HASHER,
    ):
        self._unit_of_work = unit_of_work
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm
        self._access_token_expires_in = access_token_expires_in
        self._refresh_token_expires_in = refresh_token_expires_in
        self._hasher = hasher

    async def get_jwt_tokens(self, payload: UserPayload) -> dict[str, str]:
        access_token = self._get_access_token(payload)
        refresh_token = str(uuid7())
        user_id = payload.user_id
        await self._save_refresh_token_hash(user_id, refresh_token)

        return dict(access_token=access_token, refresh_token=refresh_token)

    async def verify_access_token(self, access_token: str) -> UserPayload:
        public_key = self._get_appropriate_public_key_form()
        payload = jwt.decode(
            jwt=access_token,
            key=public_key,  # type: ignore
            algorithms=[self._algorithm],
            options={"require": ["exp"]},
        )
        user_payload = UserPayload.from_dict(payload)
        return user_payload

    async def verify_refresh_token(
        self, user_id: UUID, plain_refresh_token: str, fingerprint: str
    ) -> None:
        async with self._unit_of_work as uow:
            token = await uow.jwt_repo.get_device_active_token(user_id, fingerprint)

            if token.status_id == TokenStatus.ACTIVE and self._hasher.verify(
                plain_refresh_token, token.hashed_token
            ):
                return
            else:
                await self._verify_token_was_not_compromised(
                    user_id, fingerprint, plain_refresh_token
                )

    async def _save_refresh_token_hash(self, user_id: str, refresh_token: str) -> None:
        refresh_token_hash = self._hasher.hash(refresh_token)
        expiration_time = datetime.now(tz=timezone.utc) + timedelta(
            minutes=self._refresh_token_expires_in
        )

        # TODO: Add real fingerprint hash.
        refresh_token_to_save = RefreshToken(
            user_id=user_id,
            hashed_token=refresh_token_hash,
            hashed_fingerprint="mobile phone",
            expires_at=expiration_time,
        )

        async with self._unit_of_work as uow:
            await uow.jwt_repo.save(refresh_token_to_save)

    def _get_access_token(self, payload: UserPayload) -> str:
        expiration_time = datetime.now(tz=timezone.utc) + timedelta(
            minutes=self._access_token_expires_in
        )
        payload.exp = expiration_time
        user_payload = payload.to_dict()

        private_key = self._get_appropriate_private_key_form()

        try:
            access_token = jwt.encode(
                payload=user_payload,
                key=private_key,  # type: ignore
                algorithm=self._algorithm,
            )

        except jwt.PyJWTError as e:
            raise AccessTokenGenerationError from e

        return access_token

    def _get_appropriate_private_key_form(self) -> PrivateKeyTypes:
        private_key_der = base64.b64decode(self._private_key)
        private_key = serialization.load_der_private_key(private_key_der, password=None)
        return private_key

    def _get_appropriate_public_key_form(self) -> PublicKeyTypes:
        public_key_der = base64.b64decode(self._public_key)
        public_key = serialization.load_der_public_key(public_key_der)
        return public_key

    async def _verify_token_was_not_compromised(
        self,
        user_id: UUID,
        fingerprint: str,
        plain_refresh_token: str,
    ) -> None:
        async with self._unit_of_work as uow:
            tokens = await uow.jwt_repo.get_device_blacklisted_token_family(
                user_id, fingerprint
            )

            if tokens:
                for token in tokens:
                    if self._hasher.verify(plain_refresh_token, token.hashed_token):
                        await uow.jwt_repo.mark_tokens_as_compromised(
                            user_id=user_id,
                            fingerprint=fingerprint,
                        )
