import base64
from datetime import datetime, timezone
from typing import Any, Self
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

from src.application.dto import RefreshToken, UserPayload
from src.application.hasher import HASHER
from src.application.interfaces.repositories.jwt import IJWTRepo
from src.application.interfaces.unit_of_work import IUnitOfWork
from src.application.use_cases.jwt import JWTUseCase
from src.core.config import settings


class FakeJWTRepo(IJWTRepo):
    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshToken:
        hashed_refresh_token = HASHER.hash("18f47b4-5c2a-7b80-8f3c-92a1d4e6f8b0")
        return RefreshToken(
            user_id="019b4a71-173e-7f64-a840-9e8b042658cd",
            hashed_token=hashed_refresh_token,
            # Expiration time must be greater than (now - leeway).
            expires_at=datetime(7049, 1, 1, tzinfo=timezone.utc),
            hashed_fingerprint="mobile_phone",
            status_id=1,
        )

    async def save(self, refresh_token: RefreshToken) -> None:
        pass

    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str):
        pass

    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshToken] | None:
        pass


class FakeUnitOfWork(IUnitOfWork):
    async def __aenter__(self) -> Self:
        self.jwt_repo: IJWTRepo = FakeJWTRepo()
        return await super().__aenter__()

    def readonly(self) -> Any:
        return self

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass


@pytest.fixture
def jwt_use_case():
    return JWTUseCase(
        unit_of_work=FakeUnitOfWork(),
        private_key=settings.jwt.private_key,
        public_key=settings.jwt.public_key,
        algorithm=settings.jwt.algorithm,
        access_token_expires_in=settings.jwt.access_token_expires_in,
        refresh_token_expires_in=settings.jwt.refresh_token_expires_in,
    )


@pytest.mark.asyncio
async def test_get_jwt_tokens_was_successful(jwt_use_case: JWTUseCase):
    sut = jwt_use_case
    expected_payload = UserPayload(
        user_id="019b4a71-173e-7f64-a840-9e8b042658cd",
        is_superuser=False,
        exp=None,
    )
    result = await sut.get_jwt_tokens(expected_payload)
    public_key_der = base64.b64decode(settings.jwt.public_key)
    public_key = serialization.load_der_public_key(public_key_der)
    payload = jwt.decode(
        jwt=result["access_token"],
        key=public_key,  # type: ignore
        algorithms=[settings.jwt.algorithm],
        options={"require": ["exp"]},
    )

    assert result.keys() == {"access_token", "refresh_token"}
    assert _is_uuid(result["refresh_token"])
    assert payload["user_id"] == expected_payload.user_id
    assert payload["is_superuser"] == expected_payload.is_superuser


@pytest.mark.asyncio
async def test_verify_access_token_was_successful(jwt_use_case: JWTUseCase):
    sut = jwt_use_case
    expected_payload = UserPayload(
        user_id="019b4a71-173e-7f64-a840-9e8b042658cd",
        is_superuser=False,
        # Expiration time must be greater than (now - leeway).
        exp=datetime(7049, 1, 1, tzinfo=timezone.utc),
    )
    access_token = (
        "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
        "eyJ1c2VyX2lkIjoiMDE5YjRhNzEtMTczZS03Z"
        "jY0LWE4NDAtOWU4YjA0MjY1OGNkIiwiaXNfc3VwZX"
        "J1c2VyIjpmYWxzZSwiZXhwIjoxNjAyNzc3ODg4MDB9."
        "Quu1rKO3N8UGfwhv-6Hf-0mf-OPRq0-8VWC9avgIVuU"
        "6PWpigmaRo3GuHYalglzUCV07y4cBNlZmbBJXGHT6Dw"
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
