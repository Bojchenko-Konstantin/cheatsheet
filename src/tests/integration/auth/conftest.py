from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.hasher import HASHER

TEST_PASSWORD = "Passw0rd%"


@pytest_asyncio.fixture
async def populate_db_for_multiple_users() -> AsyncGenerator[None]:
    session = DEFAULT_SESSION_FACTORY()
    await _populate_users_for_auth_test(session)

    yield

    await _truncate_all_tables(session)


async def _populate_users_for_auth_test(session: AsyncSession) -> None:
    password = HASHER.hash(TEST_PASSWORD)
    query = text(
        """INSERT INTO "user"(user_name, is_verified, is_active,
                              is_superuser, email, hashed_password)
           VALUES (:user_name, :is_verified, :is_active,
                   :is_superuser, :email, :hashed_password)
           RETURNING user_id"""
    )

    users_to_create = [
        {
            "user_name": "active_user",
            "is_verified": True,
            "is_active": True,
            "is_superuser": False,
            "email": "test@random.mail",
            "hashed_password": password,
        },
        {
            "user_name": "inactive_user",
            "is_verified": True,
            "is_active": False,
            "is_superuser": False,
            "email": "test@random.mail",
            "hashed_password": password,
        },
        {
            "user_name": "test_password_update",
            "is_verified": True,
            "is_active": True,
            "is_superuser": False,
            "email": "update-password@test",
            "hashed_password": password,
        },
    ]

    for user in users_to_create:
        result = await session.execute(query, user)
        result.scalar_one()

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
