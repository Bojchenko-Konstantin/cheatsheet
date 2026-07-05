import base64
from datetime import datetime, timezone
from typing import Self
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

from src.application.dto import RefreshTokenRecord, UserPayload
from src.application.interfaces import ITokenRepo, IUnitOfWork
from src.core.config import settings
from src.infrastructure.hasher import HASHER
from src.infrastructure.services import TokenService
from src.infrastructure.services.jwt_core_service import JWTCoreService


class FakeTokenRepo(ITokenRepo):
    async def get_user_payload_by_hash(
        self, hashed_token: str, hashed_fingerprint: str
    ) -> UserPayload:
        return UserPayload(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"), is_superuser=False
        )

    async def save(self, token_record: RefreshTokenRecord) -> None:
        pass

    async def mark_as_compromised(self, hashed_token: str) -> None:
        pass

    async def is_token_in_blacklist(self, hashed_token: str) -> bool:
        return False

    async def revoke_token(self, hashed_token: str, hashed_fingerprint: str) -> None:
        pass

    async def revoke_all_tokens(self, user_id: UUID) -> None:
        pass


class FakeUnitOfWork(IUnitOfWork):
    def __init__(self):
        self.token_repo = FakeTokenRepo()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def readonly(self) -> Self:
        return self

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass


@pytest.fixture
def jwt_core_service() -> JWTCoreService:
    return JWTCoreService(
        private_key=settings.jwt.private_key,
        public_key=settings.jwt.public_key,
        algorithm=settings.jwt.algorithm,
        issuer=settings.jwt.issuer,
        audience=settings.jwt.audience,
    )


@pytest.fixture
def token_service(jwt_core_service: JWTCoreService) -> TokenService:
    return TokenService(
        jwt_core=jwt_core_service,
        access_token_expires_in=settings.jwt.access_token_expires_in,
        refresh_token_expires_in=settings.jwt.refresh_token_expires_in,
        unit_of_work=FakeUnitOfWork(),
        hasher=HASHER,
    )


@pytest.mark.asyncio
async def test_generate_tokens_was_successful(token_service: TokenService):
    sut = token_service
    expected_payload = UserPayload(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        is_superuser=False,
        exp=None,
    )
    result = await sut.generate_tokens(expected_payload)
    public_key_der = base64.b64decode(settings.jwt.public_key)
    public_key = serialization.load_der_public_key(public_key_der)
    payload = jwt.decode(
        jwt=result.access_token,
        key=public_key,  # type: ignore
        algorithms=[settings.jwt.algorithm],
        issuer=settings.jwt.issuer,
        audience=settings.jwt.audience,
        options={"require": ["exp"]},
    )

    assert _is_uuid(result.refresh_token)
    assert UUID(payload["user_id"]) == expected_payload.user_id
    assert payload["is_superuser"] == expected_payload.is_superuser


@pytest.mark.asyncio
async def test_verify_access_token_was_successful(
    jwt_core_service: JWTCoreService, token_service: TokenService
):
    sut = token_service

    access_token = jwt_core_service.generate_token(
        payload={
            "user_id": "019b4a71-173e-7f64-a840-9e8b042658cd",
            "is_superuser": False,
            "provider": "local",
        },
        token_type="access",
        expires_in_minutes=10,
    )

    public_key_der = base64.b64decode(settings.jwt.public_key)
    public_key = serialization.load_der_public_key(public_key_der)
    decoded = jwt.decode(
        jwt=access_token,
        key=public_key,  # type: ignore[arg-type]
        issuer=settings.jwt.issuer,
        audience=settings.jwt.audience,
        algorithms=[settings.jwt.algorithm],
    )

    expected_payload = UserPayload(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        is_superuser=False,
        exp=datetime.fromtimestamp(decoded["exp"], tz=timezone.utc),
    )

    payload = await sut.verify_access_token(access_token)

    assert payload == expected_payload


def _is_uuid(uuid_str: str) -> bool:
    try:
        UUID(uuid_str)
    except ValueError:
        return False
    else:
        return True
