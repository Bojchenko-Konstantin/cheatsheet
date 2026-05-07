import asyncio
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import Row, TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
    test_password: str,
):
    # Arrange.
    data_for_login = {
        "username": "active_user",
        "password": test_password,
    }

    user_data = await _get_user_from_db_by_username("active_user", session)
    user_id = user_data["user_id"]

    login_response = await async_client.post("/login", data=data_for_login)
    login_response_data = login_response.json()
    old_refresh_token = login_response_data["refresh_token"]
    old_access_token = login_response_data["access_token"]

    await asyncio.sleep(1)

    refresh_request_data = {
        "refresh_token": old_refresh_token,
        "fingerprint": "mobile phone",
        "user_id": user_id,
    }

    # Act.
    response = await async_client.post("/refresh", json=refresh_request_data)
    response_data = response.json()
    new_refresh_token = response_data["refresh_token"]
    new_access_token = response_data["access_token"]

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert old_access_token != new_access_token
    assert old_refresh_token != new_refresh_token


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_was_not_found_when_token_does_not_exist(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
):
    # Arrange.
    user_data = await _get_user_from_db_by_username("active_user", session)
    user_id = user_data["user_id"]

    refresh_request_data = {
        "refresh_token": "non-existent-token",
        "fingerprint": "mobile phone",
        "user_id": user_id,
    }

    # Act.
    response = await async_client.post("/refresh", json=refresh_request_data)
    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response_data["detail"] == "Failed to authorize"


async def _get_user_from_db_by_username(
    username: str, session: AsyncSession
) -> dict[str, Any]:
    async with session:
        query = _build_user_query()
        result = await session.execute(query, {"user_name": username})
        db_row = result.one()
        user_from_db = _create_user_from_db_row(db_row)

        return user_from_db


def _build_user_query() -> TextClause:
    return text(
        """
    SELECT user_id
    FROM "user"
    WHERE user_name = :user_name
    """
    )


def _create_user_from_db_row(db_row: Row) -> dict[str, Any]:
    return dict(
        user_id=str(db_row.user_id),
    )
