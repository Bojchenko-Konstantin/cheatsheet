from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.hasher import HASHER


@pytest_asyncio.fixture
async def populate_db_for_multiple_users() -> AsyncGenerator[None]:
    session = DEFAULT_SESSION_FACTORY()
    await _populate_users_for_auth_test(session)

    yield

    await _truncate_all_tables(session)


async def _populate_users_for_auth_test(session: AsyncSession) -> None:
    password = HASHER.hash("password")
    query = text(
        """INSERT INTO "user"(user_name, is_verified, is_active,
                              is_superuser, email, hashed_password)
           VALUES (:user_name, :is_verified, :is_active,
                   :is_superuser, :email, :hashed_password)"""
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
    ]

    for user in users_to_create:
        await session.execute(query, user)

    await session.commit()


async def _truncate_all_tables(session: AsyncSession) -> None:
    query = text(
        """TRUNCATE cheatsheet,
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
