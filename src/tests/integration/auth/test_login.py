from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import Row, TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.hasher import HASHER


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    test_password: str,
):
    data_for_login = {
        "username": "active_user",
        "password": test_password,
    }

    response = await async_client.post("/login", data=data_for_login)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert {"access_token", "refresh_token", "token_type"} == response_data.keys()
    assert response_data["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_was_unsuccessful_with_nonexistent_username(
    populate_db_for_multiple_users: None, async_client: AsyncClient, test_password: str
):
    data_for_login = {
        "username": "random",
        "password": test_password,
    }

    response = await async_client.post("/login", data=data_for_login)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_with_incorrect_password_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
):
    data_for_login = {
        "username": "active_user",
        "password": "Incorrect_p@ssw0rd",
    }

    response = await async_client.post("/login", data=data_for_login)

    user = await _get_user_from_db_by_username("active_user", session)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not HASHER.verify("incorrect_password", user["hashed_password"])


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_by_inactive_user_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
    test_password: str,
):
    data_for_login = {
        "username": "inactive_user",
        "password": test_password,
    }

    response = await async_client.post("/login", data=data_for_login)

    user = await _get_user_from_db_by_username("inactive_user", session)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not user["is_active"]


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
    SELECT user_name, hashed_password, is_active
    FROM "user"
    WHERE user_name = :user_name
    """
    )


def _create_user_from_db_row(db_row: Row) -> dict[str, Any]:
    return dict(
        user_name=db_row.user_name,
        hashed_password=db_row.hashed_password,
        is_active=db_row.is_active,
    )
