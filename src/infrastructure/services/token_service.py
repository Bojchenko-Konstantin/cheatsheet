from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from uuid_extensions import uuid7

from src.application.dto import RefreshTokenRecord, TokenStatus, UserPayload
from src.application.exceptions import (
    AccessTokenException,
    AccessTokenExpiredError,
    AccessTokenGenerationError,
    RefreshTokenCompromisedError,
    RefreshTokenNotFoundError,
    RevokeRefreshTokenError,
    UserNotFoundError,
)
from src.application.interfaces import ITokenService, IUnitOfWork
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.hasher import HASHER
from src.infrastructure.services import JWTCoreService


class TokenService(ITokenService):
    """Handles all operations with access (JWT) and refresh (UUIDv7) tokens."""

    def __init__(
        self,
        jwt_core: JWTCoreService,
        access_token_expires_in: int,
        refresh_token_expires_in: int,
        unit_of_work: IUnitOfWork = SQLAlchemyUnitOfWork(),
        hasher: PasswordHash = HASHER,
    ):
        self._jwt_core = jwt_core
        self._unit_of_work = unit_of_work
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
        try:
            payload = self._jwt_core.verify_token(
                token=access_token,
                expected_type="access",
                required_claims=["exp", "provider", "iss", "aud"],
            )
        except jwt.ExpiredSignatureError as e:
            raise AccessTokenExpiredError from e
        except jwt.InvalidTokenError as e:
            raise AccessTokenException from e
        except Exception as e:
            raise AccessTokenException from e

        user_payload = UserPayload.create(
            user_id=payload["user_id"],
            is_superuser=payload["is_superuser"],
            exp=payload["exp"],
            provider=payload["provider"],
        )

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
                    uow=self._unit_of_work,
                    user_id=user_id,
                    fingerprint=fingerprint,
                    plain_refresh_token=plain_refresh_token,
                )

    async def revoke_refresh_token(
        self, user_id: UUID, plain_refresh_token: str, fingerprint: str
    ) -> None:
        try:
            async with self._unit_of_work.readonly() as uow:
                await uow.user_repo.get_by_id(user_id)
        except UserNotFoundError:
            raise

        try:
            async with self._unit_of_work.readonly() as uow:
                token_record = await uow.token_repo.get_device_active_token(
                    user_id, fingerprint
                )
        except RefreshTokenNotFoundError:
            return

        if not self._hasher.verify(plain_refresh_token, token_record.hashed_token):
            return

        try:
            async with self._unit_of_work as uow:
                await uow.token_repo.revoke_token(
                    user_id=user_id,
                    fingerprint=fingerprint,
                    hashed_token=token_record.hashed_token,
                )
        except RevokeRefreshTokenError:
            raise
        except Exception as e:
            raise RevokeRefreshTokenError from e

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        async with self._unit_of_work as uow:
            await uow.token_repo.revoke_all_tokens_for_user(user_id)
            await uow._commit()

    def _generate_access_token(self, payload: UserPayload) -> str:
        try:
            access_token = self._jwt_core.generate_token(
                payload={
                    "user_id": str(payload.user_id),
                    "is_superuser": payload.is_superuser,
                    "provider": payload.provider,
                },
                token_type="access",
                expires_in_minutes=self._access_token_expires_in,
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
