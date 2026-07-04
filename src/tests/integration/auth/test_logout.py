import hashlib
import hmac
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.token import TokenStatus
from src.core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_logout_was_successful(
    populate_db_for_multiple_users: None,
    async_client: AsyncClient,
    session: AsyncSession,
    data_to_login_active_user: dict[str, str],
):
    # Arrange.
    login_response = await async_client.post("/login", data=data_to_login_active_user)
    refresh_token = login_response.cookies.get("refresh_token")

    assert refresh_token is not None

    user = await _get_user_from_db_by_username(
        data_to_login_active_user["username"], session
    )

    logout_data = {
        "fingerprint": "mobile phone",
    }

    # Act.
    async_client.cookies["refresh_token"] = refresh_token
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
    assert revoked_token["status_id"] == TokenStatus.REVOKED
    assert revoked_token["user_id"] == user["user_id"]


async def _get_user_from_db_by_username(
    username: str, session: AsyncSession
) -> dict[str, Any]:
    async with session:
        query = text(
            """
            SELECT user_id, user_name, hashed_password, is_active
            FROM "user"
            JOIN registered_user USING (user_id)
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
    hashed_token = _hash_refresh_token(refresh_token)
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
            if hashed_token == row.hashed_token:
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
    hashed_token = _hash_refresh_token(refresh_token)
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
            if hashed_token == row.hashed_token:
                return {
                    "user_id": row.user_id,
                    "hashed_token": row.hashed_token,
                    "hashed_fingerprint": row.hashed_fingerprint,
                    "status_id": row.status_id,
                    "revoked_at": row.revoked_at,
                }
        return None


def _hash_refresh_token(plain_token: str) -> str:
    return hmac.new(
        key=settings.jwt.refresh_token_secret.encode(),
        msg=plain_token.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
