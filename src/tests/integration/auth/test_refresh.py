import asyncio

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    data_to_login_active_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post("/login", data=data_to_login_active_user)
    login_response_data = login_response.json()
    old_access_token = login_response_data["access_token"]
    refresh_token = login_response.cookies.get("refresh_token")

    assert refresh_token is not None

    await asyncio.sleep(1)

    refresh_request_data = {
        "fingerprint": "mobile phone",
    }

    async_client.cookies["refresh_token"] = refresh_token

    # Act.
    response = await async_client.post("/refresh", json=refresh_request_data)
    response_data = response.json()
    new_access_token = response_data["access_token"]

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert old_access_token != new_access_token
    assert "refresh_token" in response.cookies
