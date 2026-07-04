import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import NoReturn
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from uuid_extensions import uuid7

from src.application.dto import RefreshTokenRecord, TokenPair, UserPayload
from src.application.exceptions import (
    AccessTokenException,
    AccessTokenExpiredError,
    AccessTokenGenerationError,
    RefreshTokenCompromisedError,
    RefreshTokenNotFoundError,
    RevokeRefreshTokenError,
)
from src.application.interfaces import ITokenService, IUnitOfWork
from src.core.config import settings
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
        self._secret_key = settings.jwt.refresh_token_secret
        self._hasher = hasher

    async def generate_tokens(self, payload: UserPayload) -> TokenPair:
        """Create tokens and save refresh token to database."""
        access_token = self._generate_access_token(payload)
        refresh_token = self._generate_refresh_token()
        await self._save_refresh_token_hash(payload.user_id, refresh_token)

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

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
        self, plain_refresh_token: str, fingerprint: str
    ) -> UserPayload:
        hashed_token = self._hash_refresh_token(plain_refresh_token)

        async with self._unit_of_work.readonly() as uow:
            payload = await uow.token_repo.get_user_payload_by_hash(
                hashed_token, fingerprint
            )

        if not payload:
            await self._verify_token_was_not_compromised(
                hashed_token=hashed_token,
                fingerprint=fingerprint,
            )

        return payload

    async def revoke_refresh_token(
        self, plain_refresh_token: str, fingerprint: str
    ) -> None:
        hashed_token = self._hash_refresh_token(plain_refresh_token)

        try:
            async with self._unit_of_work as uow:
                await uow.token_repo.revoke_token(
                    hashed_token=hashed_token, fingerprint=fingerprint
                )
        except (RevokeRefreshTokenError, RefreshTokenNotFoundError):
            raise
        except Exception as e:
            raise RevokeRefreshTokenError from e

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        async with self._unit_of_work as uow:
            await uow.token_repo.revoke_all_tokens(user_id)
            await uow._commit()

    def _generate_refresh_token(self) -> str:
        return str(uuid7())

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

    async def _save_refresh_token_hash(self, user_id: UUID, refresh_token: str) -> None:
        refresh_token_hash = self._hash_refresh_token(refresh_token)
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

    def _hash_refresh_token(self, plain_token: str) -> str:
        return hmac.new(
            key=self._secret_key.encode(),
            msg=plain_token.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

    async def _verify_token_was_not_compromised(
        self,
        hashed_token: str,
        fingerprint: str,
    ) -> NoReturn:
        async with self._unit_of_work.readonly() as uow:
            is_blacklisted = await uow.token_repo.is_token_in_blacklist(
                hashed_token, fingerprint
            )

        if not is_blacklisted:
            raise RefreshTokenNotFoundError

        async with self._unit_of_work as uow:
            await uow.token_repo.mark_as_compromised(
                hashed_token=hashed_token,
                fingerprint=fingerprint,
            )
        raise RefreshTokenCompromisedError
