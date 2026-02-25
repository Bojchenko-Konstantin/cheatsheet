from typing import Any, Self
from uuid import UUID

import pytest

from application.hasher import HASHER
from src.application.dto import User, UserPayload
from src.application.interfaces.repositories.user import IUserRepo
from src.application.interfaces.unit_of_work import IUnitOfWork
from src.application.use_cases.user import UserUseCase


class FakeUserRepo(IUserRepo):
    PASSWORD_HASH = HASHER.hash("password")

    async def get_by_user_name(self, user_name: str) -> User:
        return User(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            hashed_password=self.PASSWORD_HASH,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )

    async def get_by_id(self, user_id: UUID) -> User:
        return User(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            user_name="test",
            hashed_password=self.PASSWORD_HASH,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        return UserPayload(
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            is_superuser=False,
            exp=None,
        )

    async def update(self, update_data: dict[str, Any]):
        pass


class FakeUnitOfWork(IUnitOfWork):
    async def __aenter__(self) -> Self:
        self.user_repo: IUserRepo = FakeUserRepo()
        return await super().__aenter__()

    def readonly(self) -> Any:
        return self

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass


@pytest.fixture
def user_use_case():
    return UserUseCase(unit_of_work=FakeUnitOfWork())


async def test_get_user_by_user_name_was_successful(user_use_case: UserUseCase):
    sut = user_use_case
    user_name = "test"
    expected_user = User(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        user_name="test",
        hashed_password=FakeUserRepo.PASSWORD_HASH,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )

    user = await sut.get_by_user_name(user_name)

    assert user == expected_user


async def test_get_user_by_id_was_successful(user_use_case: UserUseCase):
    user_id = UUID("019b4a71-173e-7f64-a840-9e8b042658cd")
    sut = user_use_case
    expected_user = User(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        user_name="test",
        hashed_password=FakeUserRepo.PASSWORD_HASH,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )

    user = await sut.get_by_id(user_id)

    assert user == expected_user


async def test_create_user_was_successful(user_use_case: UserUseCase):
    sut = user_use_case
    create_data = dict(
        username="test",
        email="test@email.com",
        first_name="test",
        last_name="test",
        profile_description="",
        image_url="",
        social_network_id=[1],
        profile_url="",
        password="password",
        password_confirmation="password",
    )
    expected_payload = UserPayload(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        is_superuser=False,
        exp=None,
    )

    user_payload = await sut.create(create_data)

    assert user_payload == expected_payload


async def test_authenticate_user_was_successful(user_use_case: UserUseCase):
    user_name = "test"
    plain_password = "password"
    sut = user_use_case
    expected_user = User(
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        user_name="test",
        hashed_password=FakeUserRepo.PASSWORD_HASH,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )

    user = await sut.authenticate_user(user_name, plain_password)

    assert user == expected_user
