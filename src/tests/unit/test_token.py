import base64
from datetime import datetime, timezone
from typing import Self
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

from src.application.dto import RefreshTokenRecord, TokenStatus, UserPayload
from src.application.interfaces import ITokenRepo, IUnitOfWork
from src.core.config import settings
from src.infrastructure.hasher import HASHER
from src.infrastructure.services import TokenService
from src.infrastructure.services.jwt_core_service import JWTCoreService


class FakeTokenRepo(ITokenRepo):
    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshTokenRecord:
        hashed_refresh_token = HASHER.hash("18f47b4-5c2a-7b80-8f3c-92a1d4e6f8b0")
        return RefreshTokenRecord(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            hashed_token=hashed_refresh_token,
            # Expiration time must be greater than (now - leeway).
            expires_at=datetime(7049, 1, 1, tzinfo=timezone.utc),
            hashed_fingerprint="mobile_phone",
            status_id=TokenStatus.ACTIVE,
        )

    async def save(self, token_record: RefreshTokenRecord) -> None:
        pass

    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str) -> None:
        pass

    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshTokenRecord] | None:
        return None

    async def revoke_token(
        self, user_id: UUID, fingerprint: str, hashed_token: str
    ) -> None:
        pass

    async def revoke_all_tokens_for_user(self, user_id: UUID) -> None:
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
        jwt=result["access_token"],
        key=public_key,  # type: ignore
        algorithms=[settings.jwt.algorithm],
        issuer=settings.jwt.issuer,
        audience=settings.jwt.audience,
        options={"require": ["exp"]},
    )

    assert result.keys() == {"access_token", "refresh_token"}
    assert _is_uuid(result["refresh_token"])
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
