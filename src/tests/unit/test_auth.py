from typing import Any
from uuid import UUID

import pytest

from src.application.dto import (
    PasswordResetData,
    TokenPair,
    User,
    UserPayload,
)
from src.application.interfaces import ITokenService, IUserService
from src.application.use_cases import AuthUseCase


class FakeTokenService(ITokenService):
    async def generate_tokens(self, payload: UserPayload) -> TokenPair:
        return TokenPair(
            access_token=(
                "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
                "eyJ1c2VyX2lkIjoiMDE5YjRhNzEtMTczZS03Z"
                "jY0LWE4NDAtOWU4YjA0MjY1OGNkIiwiaXNfc3VwZX"
                "J1c2VyIjpmYWxzZSwiZXhwIjoxNjAyNzc3ODg4MDB9."
                "Quu1rKO3N8UGfwhv-6Hf-0mf-OPRq0-8VWC9avgIVuU"
                "6PWpigmaRo3GuHYalglzUCV07y4cBNlZmbBJXGHT6Dw"
            ),
            refresh_token="019c958f-82e1-7eca-b4c0-a68043ac5ec5",
        )

    async def verify_access_token(self, access_token: str) -> UserPayload:
        return UserPayload(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"), is_superuser=False
        )

    async def verify_refresh_token(
        self, plain_token: str, hashed_fingerprint: str
    ) -> UserPayload:
        return UserPayload(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"), is_superuser=False
        )

    async def revoke_refresh_token(
        self, plain_token: str, hashed_fingerprint: str
    ) -> None:
        pass

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        pass


class FakeUserService(IUserService):
    async def get_by_user_name(self, user_name: str) -> User:
        return User(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            hashed_password="password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

    async def get_by_email(self, email: str) -> User:
        return User(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            hashed_password="password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

    async def get_by_id(self, user_id: UUID) -> User:
        return User(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            hashed_password="password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        return UserPayload(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"), is_superuser=False
        )

    async def authenticate_user(self, user_login: str, password: str) -> User:
        return User(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            hashed_password="password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

    async def get_password_reset_data(self, email: str) -> PasswordResetData | None:
        return PasswordResetData(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            email=email,
        )

    async def get_email_by_id(self, user_id: UUID) -> str:
        return "test@example.com"

    def validate_password_strength(self, password: str) -> tuple[bool, str | None]:
        return True, None

    async def update_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        pass

    async def reset_password(self, user_id: UUID, new_password: str) -> None:
        pass

    async def verify_email(self, user_id: UUID) -> None:
        pass


@pytest.fixture
def auth_use_case():
    return AuthUseCase(FakeTokenService(), FakeUserService())


@pytest.mark.asyncio
async def test_authenticate_was_successful(auth_use_case: AuthUseCase):
    sut = auth_use_case
    user_name = "test"
    password = "password"
    result = await sut.authenticate(user_name, password)
    expected_result = TokenPair(
        access_token=(
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
            "eyJ1c2VyX2lkIjoiMDE5YjRhNzEtMTczZS03Z"
            "jY0LWE4NDAtOWU4YjA0MjY1OGNkIiwiaXNfc3VwZX"
            "J1c2VyIjpmYWxzZSwiZXhwIjoxNjAyNzc3ODg4MDB9."
            "Quu1rKO3N8UGfwhv-6Hf-0mf-OPRq0-8VWC9avgIVuU"
            "6PWpigmaRo3GuHYalglzUCV07y4cBNlZmbBJXGHT6Dw"
        ),
        refresh_token="019c958f-82e1-7eca-b4c0-a68043ac5ec5",
    )

    assert result == expected_result


@pytest.mark.asyncio
async def test_register_was_successful(auth_use_case: AuthUseCase):
    sut = auth_use_case
    create_data = {
        "username": "new_user",
        "password": "new_password",
        "password_confirmation": "new_password",
        "email": "new@example.com",
    }

    result = await sut.register(create_data)
    expected_result = TokenPair(
        access_token=(
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
            "eyJ1c2VyX2lkIjoiMDE5YjRhNzEtMTczZS03Z"
            "jY0LWE4NDAtOWU4YjA0MjY1OGNkIiwiaXNfc3VwZX"
            "J1c2VyIjpmYWxzZSwiZXhwIjoxNjAyNzc3ODg4MDB9."
            "Quu1rKO3N8UGfwhv-6Hf-0mf-OPRq0-8VWC9avgIVuU"
            "6PWpigmaRo3GuHYalglzUCV07y4cBNlZmbBJXGHT6Dw"
        ),
        refresh_token="019c958f-82e1-7eca-b4c0-a68043ac5ec5",
    )

    assert result == expected_result


@pytest.mark.asyncio
async def test_refresh_was_successful(auth_use_case: AuthUseCase):
    sut = auth_use_case
    refresh_data = {
        "user_id": UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        "refresh_token": "019c958f-82e1-7eca-b4c0-a68043ac5ec5",
        "hashed_fingerprint": "test_fingerprint",
    }

    result = await sut.refresh(refresh_data)
    expected_result = TokenPair(
        access_token=(
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
            "eyJ1c2VyX2lkIjoiMDE5YjRhNzEtMTczZS03Z"
            "jY0LWE4NDAtOWU4YjA0MjY1OGNkIiwiaXNfc3VwZX"
            "J1c2VyIjpmYWxzZSwiZXhwIjoxNjAyNzc3ODg4MDB9."
            "Quu1rKO3N8UGfwhv-6Hf-0mf-OPRq0-8VWC9avgIVuU"
            "6PWpigmaRo3GuHYalglzUCV07y4cBNlZmbBJXGHT6Dw"
        ),
        refresh_token="019c958f-82e1-7eca-b4c0-a68043ac5ec5",
    )

    assert result == expected_result


@pytest.mark.asyncio
async def test_get_current_user_was_successful(auth_use_case: AuthUseCase):
    sut = auth_use_case
    access_token = (
        "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
        "eyJ1c2VyX2lkIjoiMDE5YjRhNzEtMTczZS03Z"
        "jY0LWE4NDAtOWU4YjA0MjY1OGNkIiwiaXNfc3VwZX"
        "J1c2VyIjpmYWxzZSwiZXhwIjoxNjAyNzc3ODg4MDB9."
        "Quu1rKO3N8UGfwhv-6Hf-0mf-OPRq0-8VWC9avgIVuU"
        "6PWpigmaRo3GuHYalglzUCV07y4cBNlZmbBJXGHT6Dw"
    )

    result = await sut.get_current_user(access_token)
    expected_result = User(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        user_name="test",
        hashed_password="password",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    assert result == expected_result
