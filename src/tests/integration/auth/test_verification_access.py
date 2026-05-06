import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import Row, TextClause, text

from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.tests.integration.auth.conftest import TEST_PASSWORD


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_create_cheatsheet_by_unverified_user_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    cheatsheet_data = {
        "title": "Test Cheatsheet",
        "content": "Test content",
        "is_public": True,
        "tags": [{"tag_id": 1, "tag_name": "python"}],
    }

    # Act.
    response = await async_client.post("/cheatsheets/", json=cheatsheet_data)

    # Assert.
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Email not verified" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_update_cheatsheet_by_unverified_user_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    update_data = {
        "title": "Updated Title",
        "content": "Updated content",
        "is_public": True,
        "tags": [{"tag_id": 1, "tag_name": "python"}],
    }

    # Act.
    response = await async_client.put(
        "/cheatsheets/00000000-0000-0000-0000-000000000000",
        json=update_data,
    )

    # Assert.
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Email not verified" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_update_password_by_unverified_user_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    password_update_data = {
        "old_password": TEST_PASSWORD,
        "new_password": "NewP@ssw0rd!",
        "confirm_password": "NewP@ssw0rd!",
    }

    # Act.
    response = await async_client.put("/password", json=password_update_data)

    # Assert.
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Email not verified" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_by_unverified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }

    # Act.
    response = await async_client.post("/login", data=login_data)
    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert "refresh_token" in response_data


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_by_unverified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    tokens = login_response.json()

    user_id = await _get_user_id_from_db_by_username("unverified_user")

    refresh_data = {
        "refresh_token": tokens["refresh_token"],
        "fingerprint": "mobile phone",
        "user_id": user_id,
    }

    # Act.
    response = await async_client.post("/refresh", json=refresh_data)

    # Assert.
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_logout_by_unverified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    tokens = login_response.json()

    user_id = await _get_user_id_from_db_by_username("unverified_user")

    logout_data = {
        "user_id": user_id,
        "refresh_token": tokens["refresh_token"],
        "fingerprint": "mobile phone",
    }

    # Act.
    response = await async_client.post("/logout", json=logout_data)

    # Assert.
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_public_cheatsheet_by_unverified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange
    login_data = {
        "username": "active_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    cheatsheet_data = {
        "title": "Public Cheatsheet For Test",
        "content": "Public content",
        "is_public": True,
        "tags": [{"tag_id": 1, "tag_name": "python"}],
    }

    create_response = await async_client.post("/cheatsheets/", json=cheatsheet_data)
    cheatsheet_id = create_response.json()["cheatsheet_id"]

    login_data = {
        "username": "unverified_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    unverified_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {unverified_token}"})

    # Act.
    response = await async_client.get(f"/cheatsheets/{cheatsheet_id}")

    # Assert.
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_create_cheatsheet_by_verified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    login_data = {
        "username": "active_user",
        "password": TEST_PASSWORD,
    }
    login_response = await async_client.post("/login", data=login_data)
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    cheatsheet_data = {
        "title": "Verified User Cheatsheet",
        "content": "Created by verified user",
        "is_public": True,
        "tags": [{"tag_id": 1, "tag_name": "python"}],
    }

    # Act.
    response = await async_client.post("/cheatsheets/", json=cheatsheet_data)

    # Assert.
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_create_cheatsheet_by_guest_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
):
    # Arrange.
    cheatsheet_data = {
        "title": "Guest Cheatsheet",
        "content": "Created by guest",
        "is_public": True,
        "tags": [{"tag_id": 1, "tag_name": "python"}],
    }

    # Act.
    response = await async_client.post("/cheatsheets/", json=cheatsheet_data)

    # Assert.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def _get_user_id_from_db_by_username(username: str) -> str:
    async with DEFAULT_SESSION_FACTORY() as session:
        query = _build_user_id_query()
        result = await session.execute(query, {"user_name": username})
        db_row = result.one()
        user_from_db = _create_user_id_from_db_row(db_row)

        return user_from_db


def _build_user_id_query() -> TextClause:
    return text(
        """
    SELECT user_id
    FROM "user"
    WHERE user_name = :user_name
    """
    )


def _create_user_id_from_db_row(db_row: Row) -> str:
    return str(db_row.user_id)
