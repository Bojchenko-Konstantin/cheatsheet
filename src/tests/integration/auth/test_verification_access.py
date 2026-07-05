import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_create_cheatsheet_by_unverified_user_was_unsuccessful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    data_to_login_unverified_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post(
        "/login", data=data_to_login_unverified_user
    )
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
    data_to_login_unverified_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post(
        "/login", data=data_to_login_unverified_user
    )
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
    data_to_login_unverified_user: dict[str, str],
):
    # Arrange.
    new_password = "NewP@ssw0rd!"
    login_response = await async_client.post(
        "/login", data=data_to_login_unverified_user
    )
    access_token = login_response.json()["access_token"]

    async_client.headers.update({"Authorization": f"Bearer {access_token}"})

    password_update_data = {
        "old_password": data_to_login_unverified_user["password"],
        "new_password": new_password,
        "confirm_password": new_password,
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
    data_to_login_unverified_user: dict[str, str],
):
    # Act.
    response = await async_client.post("/login", data=data_to_login_unverified_user)
    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert "refresh_token" in response.cookies


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_by_unverified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    data_to_login_unverified_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post(
        "/login", data=data_to_login_unverified_user
    )
    refresh_token = login_response.cookies.get("refresh_token")

    assert refresh_token is not None

    async_client.cookies["refresh_token"] = refresh_token
    refresh_data = {
        "hashed_fingerprint": "mobile phone",
    }

    # Act.
    response = await async_client.post("/refresh", json=refresh_data)

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_logout_by_unverified_user_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    data_to_login_unverified_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post(
        "/login", data=data_to_login_unverified_user
    )
    refresh_token = login_response.cookies.get("refresh_token")

    assert refresh_token is not None

    async_client.cookies["refresh_token"] = refresh_token

    logout_data = {
        "hashed_fingerprint": "mobile phone",
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
    data_to_login_active_user: dict[str, str],
    data_to_login_unverified_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post("/login", data=data_to_login_active_user)
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

    login_response = await async_client.post(
        "/login", data=data_to_login_unverified_user
    )

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
    data_to_login_active_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post("/login", data=data_to_login_active_user)
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
