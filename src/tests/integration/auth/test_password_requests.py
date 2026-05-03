import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text

from src.application.exceptions.user import PasswordsDontMatchError
from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.hasher import HASHER


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_password_update_was_successful(
    async_client: AsyncClient, populate_db_for_multiple_users: None
):
    # Arrange.
    login_data = {
        "username": "test_password_update",
        "password": "password",
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    expected_password = "New_password123%"
    data_for_password_change = {
        "old_password": "password",
        "new_password": "New_password123%",
        "confirm_password": "New_password123%",
    }

    # Act.
    response = await async_client.put("/password", json=data_for_password_change)
    new_password_hash = await _get_password_from_db_by_username(login_data["username"])

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert HASHER.verify(expected_password, new_password_hash)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_weak_password_update_was_unsuccessful(
    async_client: AsyncClient, populate_db_for_multiple_users: None
):
    # Arrange.
    login_data = {
        "username": "test_password_update",
        "password": "password",
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    data_for_password_change = {
        "old_password": "password",
        "new_password": "weak_password",
        "confirm_password": "weak_password",
    }

    # Act.
    response = await async_client.put("/password", json=data_for_password_change)

    # Assert.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Password must contain at least one digit" in response.text


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_passwords_did_not_match_and_update_was_unsuccessful(
    async_client: AsyncClient, populate_db_for_multiple_users: None
):
    # Arrange.
    login_data = {
        "username": "test_password_update",
        "password": "password",
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    data_for_password_change = {
        "old_password": "password",
        "new_password": "ranDom_password123!",
        "confirm_password": "wRong_password123!",
    }

    # Act.
    with pytest.raises(PasswordsDontMatchError):
        await async_client.put("/password", json=data_for_password_change)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_incorrect_current_password_update_was_unsuccessful(
    async_client: AsyncClient, populate_db_for_multiple_users: None
):
    # Arrange.
    login_data = {
        "username": "test_password_update",
        "password": "password",
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    data_for_password_change = {
        "old_password": "wrong_password",
        "new_password": "New_password123!",
        "confirm_password": "New_password123!",
    }

    # Act.
    response = await async_client.put("/password", json=data_for_password_change)

    # Assert.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Current password is incorrect" in response.text


async def _get_password_from_db_by_username(username: str) -> str:
    async with DEFAULT_SESSION_FACTORY() as session:
        query = text(
            """
            SELECT hashed_password
            FROM "user"
            WHERE user_name = :user_name
            """
        )
        result = await session.execute(query, {"user_name": username})
        row = result.one()

        return row.hashed_password
