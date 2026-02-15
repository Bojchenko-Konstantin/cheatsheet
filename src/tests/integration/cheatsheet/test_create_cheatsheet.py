from typing import Any

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy import Row, text
from sqlalchemy.sql.elements import TextClause

from src.api.v1.routers.auth import get_current_user
from src.application.dto import User
from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.tests.integration.cheatsheet.conftest import CheatsheetTestRecord


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_created_cheatsheet_persists_to_database(
    populate_db_for_single_cheatsheet: CheatsheetTestRecord,
    async_client: AsyncClient,
    app: FastAPI,
):
    # Arrange.
    _, user_id, tags = populate_db_for_single_cheatsheet

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

    app.dependency_overrides[get_current_user] = override_get_current_user

    data_for_new_cheatsheet = {
        "title": "Test Cheatsheet",
        "content": "Test content",
        "is_public": True,
        "tags": tags,
    }

    # Act.
    response = await async_client.post("/cheatsheets/", json=data_for_new_cheatsheet)

    async with DEFAULT_SESSION_FACTORY() as session:
        query = _build_cheatsheet_query()
        result = await session.execute(query, {"title": "Test Cheatsheet"})
        db_row = result.one()
        expected_result = _create_cheatsheet_from_db_row(db_row)

    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_201_CREATED
    assert response_data == expected_result


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
        JOIN cheatsheet_stats cs ON c.cheatsheet_id = cs.cheatsheet_id
        LEFT JOIN cheatsheet_to_tag ctt ON c.cheatsheet_id = ctt.cheatsheet_id
        LEFT JOIN md_tag t ON ctt.tag_id = t.tag_id
        WHERE c.title = :title
        GROUP BY c.cheatsheet_id, cs.count_like, cs.count_view
    """
    )


def _create_cheatsheet_from_db_row(db_row: Row) -> dict[str, Any]:
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
