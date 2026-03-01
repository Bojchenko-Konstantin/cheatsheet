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

from src.application.dto import RefreshTokenRecord, TokenStatus, UserPayload
from src.application.exceptions import (
    AccessTokenException,
    AccessTokenExpiredError,
    AccessTokenGenerationError,
    RefreshTokenCompromisedError,
)
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.unit_of_work import IUnitOfWork
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.hasher import HASHER


class TokenService(ITokenService):
    """Handles all operations with access (JWT) and refresh (UUIDv7) tokens."""

    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str,
        access_token_expires_in: int,
        refresh_token_expires_in: int,
        unit_of_work: IUnitOfWork = SQLAlchemyUnitOfWork(),
        hasher: PasswordHash = HASHER,
    ):
        self._unit_of_work = unit_of_work
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm
        self._access_token_expires_in = access_token_expires_in
        self._refresh_token_expires_in = refresh_token_expires_in
        self._hasher = hasher

    async def generate_tokens(self, payload: UserPayload) -> dict[str, str]:
        """Create tokens and save refresh token to database."""
        access_token = self._generate_access_token(payload)
        refresh_token = self._generate_refresh_token()
        await self._save_refresh_token_hash(payload.user_id, refresh_token)

        return dict(access_token=access_token, refresh_token=refresh_token)

    def _generate_refresh_token(self) -> str:
        return str(uuid7())

    async def verify_access_token(self, access_token: str) -> UserPayload:
        public_key = self._get_appropriate_public_key_form()

        try:
            payload = jwt.decode(
                jwt=access_token,
                key=public_key,  # type: ignore
                algorithms=[self._algorithm],
                options={"require": ["exp"]},
            )
        except jwt.ExpiredSignatureError as e:
            raise AccessTokenExpiredError from e
        except jwt.InvalidTokenError as e:
            raise AccessTokenException from e
        except Exception as e:
            raise AccessTokenException from e

        user_payload = UserPayload.create(**payload)

        return user_payload

    async def verify_refresh_token(
        self, user_id: UUID, plain_refresh_token: str, fingerprint: str
    ) -> None:
        async with self._unit_of_work as uow:
            token_record = await uow.token_repo.get_device_active_token(
                user_id, fingerprint
            )

            if self._is_valid_refresh_token(token_record, plain_refresh_token):
                return
            else:
                await self._verify_token_was_not_compromised(
                    uow=uow,
                    user_id=user_id,
                    fingerprint=fingerprint,
                    plain_refresh_token=plain_refresh_token,
                )

    def _generate_access_token(self, payload: UserPayload) -> str:
        expiration_time = datetime.now(tz=timezone.utc) + timedelta(
            minutes=self._access_token_expires_in
        )
        payload.exp = expiration_time
        user_payload = payload.to_payload()

        private_key = self._get_appropriate_private_key_form()

        try:
            access_token = jwt.encode(
                payload=user_payload,
                key=private_key,  # type: ignore
                algorithm=self._algorithm,
            )
        except jwt.PyJWTError as e:
            raise AccessTokenGenerationError from e
        except Exception as e:
            raise AccessTokenException from e

        return access_token

    def _is_valid_refresh_token(
        self, token_record: RefreshTokenRecord, plain_refresh_token: str
    ) -> bool:
        return token_record.status_id == TokenStatus.ACTIVE and self._hasher.verify(
            plain_refresh_token, token_record.hashed_token
        )

    async def _save_refresh_token_hash(self, user_id: UUID, refresh_token: str) -> None:
        refresh_token_hash = self._hasher.hash(refresh_token)
        expiration_time = datetime.now(tz=timezone.utc) + timedelta(
            minutes=self._refresh_token_expires_in
        )

        # TODO: Add real fingerprint hash.
        token_record = RefreshTokenRecord(
            user_id=user_id,
            hashed_token=refresh_token_hash,
            hashed_fingerprint="mobile phone",
            expires_at=expiration_time,
        )

        async with self._unit_of_work as uow:
            await uow.token_repo.save(token_record)

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
        uow: IUnitOfWork,
        user_id: UUID,
        fingerprint: str,
        plain_refresh_token: str,
    ) -> None:
        token_records = await uow.token_repo.get_device_blacklisted_token_family(
            user_id, fingerprint
        )

        if not token_records:
            return

        for record in token_records:
            if not self._is_valid_token(plain_refresh_token, record.hashed_token):
                continue

            await uow.token_repo.mark_tokens_as_compromised(
                user_id=user_id,
                fingerprint=fingerprint,
            )
            raise RefreshTokenCompromisedError

    def _is_valid_token(self, plain_refresh_token: str, hashed_refresh_token: str):
        return self._hasher.verify(plain_refresh_token, hashed_refresh_token)
