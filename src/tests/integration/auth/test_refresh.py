import asyncio
import hashlib
import hmac

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.token import TokenStatus
from src.core.config import settings


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


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_token_was_marked_compromised_successfully(
    populate_db_for_multiple_users: None,
    session: AsyncSession,
    async_client: AsyncClient,
    data_to_login_active_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post("/login", data=data_to_login_active_user)
    refresh_token = login_response.cookies.get("refresh_token")
    refresh_request_data = {
        "fingerprint": "mobile phone",
    }
    assert refresh_token is not None

    # First refresh with active token.
    async_client.cookies["refresh_token"] = refresh_token
    await async_client.post("/refresh", json=refresh_request_data)

    # Act.
    # Second request with already revoked token.
    await async_client.post("/refresh", json=refresh_request_data)
    status_id = await _get_token_status_by_token(session, refresh_token)

    # Assert.
    assert status_id == TokenStatus.COMPROMISED


async def _get_token_status_by_token(session: AsyncSession, plain_token: str) -> str:
    hashed_token = _hash_refresh_token(plain_token)

    async with session:
        query = _build_query()
        result = await session.execute(query, {"hashed_token": hashed_token})
        db_row = result.one()

        return db_row.status_id


def _build_query() -> TextClause:
    return text(
        """
    SELECT status_id
    FROM refresh_token_blacklist
    WHERE hashed_token = :hashed_token
    """
    )


def _hash_refresh_token(plain_token: str) -> str:
    return hmac.new(
        key=settings.jwt.refresh_token_secret.encode(),
        msg=plain_token.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
