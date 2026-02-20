import asyncio
import base64
from typing import Any
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from fastapi import status
from httpx import AsyncClient

from src.core.config import settings


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

    public_key_der = base64.b64decode(settings.jwt.public_key)
    public_key = serialization.load_der_public_key(public_key_der)
    payload = jwt.decode(
        jwt=new_access_token,
        key=public_key,  # type: ignore
        algorithms=[settings.jwt.algorithm],
        options={"require": ["exp"]},
    )

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert old_access_token != new_access_token
    assert old_refresh_token != new_refresh_token
    assert payload["user_id"] == user_id
    assert _is_uuid(new_refresh_token)


def _is_uuid(uuid_str: str) -> bool:
    try:
        UUID(uuid_str)

    except ValueError:
        return False

    else:
        return True
