from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy import Row, TextClause, text

from src.api.dependencies import get_current_user_optional
from src.application.dto import User
from src.infrastructure.database import DEFAULT_SESSION_FACTORY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_cheatsheet_by_id_was_successful(
    populate_db_for_single_cheatsheet, async_client: AsyncClient, app: FastAPI
):
    # Arrange.
    cheatsheet_id, user_id, _ = populate_db_for_single_cheatsheet

    fake_user = User(
        user_id=user_id,
        user_name="test",
        hashed_password="password",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )

    async def override_get_current_user() -> User:
        return fake_user

    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    expected_result = await _get_cheatsheet_from_db_by_id(cheatsheet_id)

    # Act.
    response = await async_client.get(f"/cheatsheets/{str(cheatsheet_id)}")
    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert response_data == expected_result


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_cheatsheet_fails_when_id_does_not_exist(
    async_client: AsyncClient, app: FastAPI
):
    # Arrange.
    non_existent_cheatsheet_id = UUID("01998b2f-af53-7ca0-85f3-9c01093dd430")

    fake_user = User(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_name="test",
        hashed_password="password",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )

    async def override_get_current_user() -> User:
        return fake_user

    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    # Act.
    response = await async_client.get(f"/cheatsheets/{str(non_existent_cheatsheet_id)}")
    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        response_data["detail"]
        == f"Cheatsheet with id {non_existent_cheatsheet_id} was not found"
    )


async def _get_cheatsheet_from_db_by_id(cheatsheet_id: UUID) -> dict[str, Any]:
    async with DEFAULT_SESSION_FACTORY() as session:
        query = _build_cheatsheet_query()
        result = await session.execute(query, {"cheatsheet_id": cheatsheet_id})
        db_row = result.one()

        cheatsheet_from_db = _create_cheatsheet_from_db_row(db_row)
        return cheatsheet_from_db


def _build_cheatsheet_query() -> TextClause:
    return text(
        """
        SELECT
            c.cheatsheet_id,
            c.title,
            c.content,
            c.is_public,
            c.created_at,
            c.updated_at,
            cs.count_like,
            cs.count_view,
            json_agg(
                json_build_object(
                    'tag_id', t.tag_id,
                    'tag_name', t.tag_name
                )
            ) as tags
        FROM cheatsheet c
        JOIN cheatsheet_stats cs USING(cheatsheet_id)
        LEFT JOIN cheatsheet_to_tag ctt USING(cheatsheet_id)
        LEFT JOIN md_tag t USING(tag_id)
        WHERE c.cheatsheet_id = :cheatsheet_id
        GROUP BY c.cheatsheet_id, cs.count_like, cs.count_view
    """
    )


def _create_cheatsheet_from_db_row(db_row: Row) -> dict[str, str]:
    return dict(
        cheatsheet_id=str(db_row.cheatsheet_id),
        title=db_row.title,
        content=db_row.content,
        is_public=db_row.is_public,
        created_at=db_row.created_at.isoformat(),
        updated_at=db_row.updated_at.isoformat(),
        count_like=db_row.count_like,
        count_view=db_row.count_view,
        tags=db_row.tags,
    )
