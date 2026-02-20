import asyncio
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_success(
    populate_db_for_single_user: dict[str, Any],
    async_client: AsyncClient,
):
    # Arrange.
    data_for_login = {
        "username": "test",
        "password": "password",
    }

    user_data = populate_db_for_single_user
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
    access_token_parts = response_data["access_token"].split(".")

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert old_access_token != new_access_token
    assert old_refresh_token != new_refresh_token
    assert len(access_token_parts) == 3
    assert len(new_refresh_token) == 36
    assert new_refresh_token.count("-") == 4
