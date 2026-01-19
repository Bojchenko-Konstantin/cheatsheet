import pytest
from sqlalchemy import Row, text
from sqlalchemy.sql.elements import TextClause

from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import Cheatsheet, Tag
from src.infrastructure.database import DEFAULT_SESSION_FACTORY
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_created_cheatsheet_persists_to_database(
    populate_db_for_single_cheatsheet,
):
    _, user_id, tags = populate_db_for_single_cheatsheet
    sut = CheatsheetUseCase(SQLAlchemyUnitOfWork())

    data_for_new_cheatsheet = dict(
        user_id=user_id,
        title="Test Cheatsheet",
        content="Test content",
        is_public=True,
        tags=tags,
    )

    created_cheatsheet = await sut.create(data_for_new_cheatsheet)

    async with DEFAULT_SESSION_FACTORY() as session:
        query = _build_cheatsheet_query()
        result = await session.execute(query, {"title": "Test Cheatsheet"})
        db_row = result.one()

        expected_result = _create_cheatsheet_from_db_row(db_row)

    assert created_cheatsheet == expected_result


def _build_cheatsheet_query() -> TextClause:
    return text(
        """
        SELECT
            c.cheatsheet_id,
            c.user_id,
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


def _create_cheatsheet_from_db_row(db_row: Row) -> Cheatsheet:
    return Cheatsheet(
        cheatsheet_id=db_row.cheatsheet_id,
        user_id=db_row.user_id,
        title=db_row.title,
        content=db_row.content,
        is_public=db_row.is_public,
        created_at=db_row.created_at,
        updated_at=db_row.updated_at,
        count_like=db_row.count_like,
        count_view=db_row.count_view,
        tags={
            Tag(tag_id=tag["tag_id"], tag_name=tag["tag_name"]) for tag in db_row.tags
        },
    )
