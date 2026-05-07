from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.hasher import HASHER


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_logout_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
    test_password: str,
):
    # Arrange.
    login_data = {
        "username": "active_user",
        "password": test_password,
    }
    login_response = await async_client.post("/login", data=login_data)

    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    user = await _get_user_from_db_by_username("active_user", session)

    logout_data = {
        "user_id": str(user["user_id"]),
        "refresh_token": refresh_token,
        "fingerprint": "mobile phone",
    }

    # Act.
    response = await async_client.post("/logout", json=logout_data)

    active_token = await _get_refresh_token_from_db(
        refresh_token, user["user_id"], session
    )
    revoked_token = await _get_blacklisted_token_from_db(
        refresh_token, user["user_id"], session
    )

    # Assert.
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert active_token is None
    assert revoked_token is not None
    assert revoked_token["status_id"] == 2
    assert revoked_token["user_id"] == user["user_id"]


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_logout_with_nonexistent_user_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    logout_data = {
        "user_id": "00000000-0000-0000-0000-000000000000",
        "refresh_token": "some-token",
        "fingerprint": "mobile phone",
    }

    response = await async_client.post("/logout", json=logout_data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data["detail"] == "User not found"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_logout_with_invalid_refresh_token_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
):
    user = await _get_user_from_db_by_username("active_user", session)

    logout_data = {
        "user_id": str(user["user_id"]),
        "refresh_token": "invalid-token-that-doesnt-exist",
        "fingerprint": "mobile phone",
    }

    response = await async_client.post("/logout", json=logout_data)

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def _get_user_from_db_by_username(
    username: str, session: AsyncSession
) -> dict[str, Any]:
    async with session:
        query = text(
            """
            SELECT user_id, user_name, hashed_password, is_active
            FROM "user"
            WHERE user_name = :user_name
            """
        )
        result = await session.execute(query, {"user_name": username})
        row = result.one()

        return {
            "user_id": row.user_id,
            "user_name": row.user_name,
            "hashed_password": row.hashed_password,
            "is_active": row.is_active,
        }


async def _get_refresh_token_from_db(
    refresh_token: str, user_id: str, session: AsyncSession
) -> dict[str, Any] | None:
    async with session:
        query = text(
            """
            SELECT user_id, hashed_token, hashed_fingerprint, status_id
            FROM refresh_token
            WHERE user_id = :user_id AND status_id = 1
            """
        )
        result = await session.execute(query, {"user_id": user_id})
        rows = result.all()

        for row in rows:
            if HASHER.verify(refresh_token, row.hashed_token):
                return {
                    "user_id": row.user_id,
                    "hashed_token": row.hashed_token,
                    "hashed_fingerprint": row.hashed_fingerprint,
                    "status_id": row.status_id,
                }
        return None


async def _get_blacklisted_token_from_db(
    refresh_token: str, user_id: str, session: AsyncSession
) -> dict[str, Any] | None:
    async with session:
        query = text(
            """
            SELECT user_id, hashed_token, hashed_fingerprint, status_id, revoked_at
            FROM refresh_token_blacklist
            WHERE user_id = :user_id AND status_id = 2
            """
        )
        result = await session.execute(query, {"user_id": user_id})
        rows = result.all()

        for row in rows:
            if HASHER.verify(refresh_token, row.hashed_token):
                return {
                    "user_id": row.user_id,
                    "hashed_token": row.hashed_token,
                    "hashed_fingerprint": row.hashed_fingerprint,
                    "status_id": row.status_id,
                    "revoked_at": row.revoked_at,
                }
        return None
