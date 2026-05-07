from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.auth.models import DBUserData


@pytest.fixture(scope="session")
def active_user() -> Generator[DBUserData]:
    yield DBUserData(name="active_user")


@pytest.fixture(scope="session")
def inactive_user() -> Generator[DBUserData]:
    yield DBUserData(name="inactive_user", is_active=False)


@pytest.fixture(scope="session")
def unverified_user() -> Generator[DBUserData]:
    yield DBUserData(
        name="unverified_user",
        is_verified=False,
    )


@pytest.fixture(scope="session")
def nonexistent_user() -> Generator[DBUserData]:
    yield DBUserData(
        name="nonexistent_user",
        is_verified=False,
    )


@pytest.fixture(scope="session")
def update_password_user() -> Generator[DBUserData]:
    yield DBUserData(name="test_password_update", email="test_email.test")


@pytest.fixture(scope="session")
def data_to_login_active_user(active_user: DBUserData) -> Generator[dict[str, str]]:
    yield {
        "username": active_user.name,
        "password": active_user.password,
    }


@pytest.fixture(scope="session")
def data_to_login_nonexistent_user(
    nonexistent_user: DBUserData,
) -> Generator[dict[str, str]]:
    yield {
        "username": nonexistent_user.name,
        "password": nonexistent_user.password,
    }


@pytest.fixture(scope="session")
def data_to_login_inactive_user(inactive_user: DBUserData) -> Generator[dict[str, str]]:
    yield {
        "username": inactive_user.name,
        "password": inactive_user.password,
    }


@pytest_asyncio.fixture
async def populate_db_for_multiple_users(
    session: AsyncSession,
    active_user: DBUserData,
    inactive_user: DBUserData,
    unverified_user: DBUserData,
    update_password_user: DBUserData,
) -> AsyncGenerator[None]:
    await _populate_users_for_auth_test(
        session,
        active_user,
        inactive_user,
        unverified_user,
        update_password_user,
    )
    await _populate_tags(session)

    yield

    await _truncate_all_tables(session)


async def _populate_users_for_auth_test(
    session: AsyncSession,
    active_user: DBUserData,
    inactive_user: DBUserData,
    unverified_user: DBUserData,
    update_password_user: DBUserData,
) -> None:
    query = text(
        """INSERT INTO "user"(user_name, is_verified, is_active,
                              is_superuser, email, hashed_password)
           VALUES (:user_name, :is_verified, :is_active,
                   :is_superuser, :email, :hashed_password)
           RETURNING user_id"""
    )

    users_to_create = [
        {
            "user_name": active_user.name,
            "is_verified": active_user.is_verified,
            "is_active": active_user.is_active,
            "is_superuser": active_user.is_superuser,
            "email": active_user.email,
            "hashed_password": active_user.hashed_password,
        },
        {
            "user_name": inactive_user.name,
            "is_verified": inactive_user.is_verified,
            "is_active": inactive_user.is_active,
            "is_superuser": inactive_user.is_superuser,
            "email": inactive_user.email,
            "hashed_password": inactive_user.hashed_password,
        },
        {
            "user_name": update_password_user.name,
            "is_verified": update_password_user.is_verified,
            "is_active": update_password_user.is_active,
            "is_superuser": update_password_user.is_superuser,
            "email": update_password_user.email,
            "hashed_password": update_password_user.hashed_password,
        },
        {
            "user_name": unverified_user.name,
            "is_verified": unverified_user.is_verified,
            "is_active": unverified_user.is_active,
            "is_superuser": unverified_user.is_superuser,
            "email": unverified_user.email,
            "hashed_password": unverified_user.hashed_password,
        },
    ]

    for user in users_to_create:
        result = await session.execute(query, user)
        result.scalar_one()

    await session.commit()


async def _populate_tags(session: AsyncSession) -> None:
    tag_query = text(
        """INSERT INTO md_tag(tag_name)
           VALUES (:tag_name)
           ON CONFLICT (tag_name) DO NOTHING"""
    )

    tags_to_create = ["python", "javascript"]

    for tag in tags_to_create:
        await session.execute(tag_query, {"tag_name": tag})

    await session.commit()


async def _truncate_all_tables(session: AsyncSession) -> None:
    query = text(
        """TRUNCATE refresh_token_blacklist,
                    refresh_token,
                    cheatsheet,
                    "user",
                    md_tag,
                    cheatsheet_stats,
                    cheatsheet_to_tag
           RESTART IDENTITY
           CASCADE
        """
    )

    await session.execute(query)
    await session.commit()
