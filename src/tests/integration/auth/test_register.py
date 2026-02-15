from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import Row, text
from sqlalchemy.sql.elements import TextClause

from src.application.hasher import HASHER
from src.infrastructure.database.database import DEFAULT_SESSION_FACTORY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_register(
    populate_db_for_single_user: None,
    async_client: AsyncClient,
):
    # Arrange.
    data_for_register = {
        "username": "test_register",
        "email": "user@example.com",
        "first_name": "string",
        "last_name": "string",
        "profile_description": "string",
        "image_url": "string",
        "social_network_id": [0],
        "profile_url": ["string"],
        "password": "password",
        "password_confirmation": "password",
    }

    expected_result = {
        "user_name": "test_register",
        "email": "user@example.com",
        "first_name": "string",
        "last_name": "string",
        "profile_description": "string",
        "image_url": "string",
    }

    # Act.
    response = await async_client.post("/register", json=data_for_register)

    async with DEFAULT_SESSION_FACTORY() as session:
        query = _build_user_query()
        result = await session.execute(query, {"user_name": "test_register"})
        db_row = result.one()
        registered_user = _create_user_from_db_row(db_row)

    # Assert.
    assert response.status_code == status.HTTP_201_CREATED
    assert HASHER.verify("password", registered_user.pop("hashed_password"))
    assert registered_user == expected_result


def _build_user_query() -> TextClause:
    return text(
        """
        SELECT
            u.user_name,
            u.email,
            u.hashed_password,
            du.first_name,
            du.last_name,
            du.profile_description,
            du.image_url
        FROM "user" u
        JOIN user_detail du USING (user_id)
        WHERE u.user_name = :user_name
    """
    )


def _create_user_from_db_row(db_row: Row) -> dict[str, Any]:
    return dict(
        user_name=db_row.user_name,
        email=db_row.email,
        first_name=db_row.first_name,
        last_name=db_row.last_name,
        profile_description=db_row.profile_description,
        image_url=db_row.image_url,
        hashed_password=db_row.hashed_password,
    )
