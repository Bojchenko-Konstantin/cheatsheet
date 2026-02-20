from collections.abc import AsyncGenerator
from typing import Any

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.hasher import HASHER
from src.infrastructure.database import DEFAULT_SESSION_FACTORY


@pytest_asyncio.fixture
async def populate_db_for_single_user() -> AsyncGenerator[dict[str, Any]]:
    session = DEFAULT_SESSION_FACTORY()
    user_data = await _populate_user_for_auth_test(session)

    yield user_data

    await _truncate_all_tables(session)


async def _populate_user_for_auth_test(session: AsyncSession) -> dict[str, Any]:
    password = HASHER.hash("password")
    query = text(
        """INSERT INTO "user"(user_name, is_verified, is_active,
                              is_superuser, email, hashed_password)
           VALUES (:user_name, :is_verified, :is_active,
                   :is_superuser, :email, :hashed_password)
           RETURNING user_id, user_name"""
    )

    data = [
        {
            "user_name": "test",
            "is_verified": True,
            "is_active": True,
            "is_superuser": False,
            "email": "test@random.mail",
            "hashed_password": password,
        }
    ]

    result = await session.execute(query, data)
    await session.commit()

    row = result.first()
    if row is None:
        raise RuntimeError("Failed to insert test user - no row returned")

    return {
        "user_id": str(row.user_id),
        "user_name": row.user_name,
        "plain_password": "password",
    }


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
