import pytest
from sqlalchemy import text

from infrastructure.database.database import DEFAULT_SESSION_FACTORY
from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import Cheatsheet, Tag
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_create_cheatsheet_success(populate_db_for_single_cheatsheet):
    _, tags = populate_db_for_single_cheatsheet

    unit_of_work = SQLAlchemyUnitOfWork()
    sut = CheatsheetUseCase(unit_of_work)

    data_for_creation_cheatsheet = Cheatsheet(
        title="Test Cheatsheet", content="Test content", is_public=True, tags=tags
    )

    created_cheatsheet = await sut.create(data_for_creation_cheatsheet)

    async with DEFAULT_SESSION_FACTORY() as session:
        query = text(
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

        result = await session.execute(query, {"title": "Test Cheatsheet"})
        db_row = result.first()

        expected_result = Cheatsheet(
            cheatsheet_id=db_row.cheatsheet_id,  # type: ignore
            title=db_row.title,  # type: ignore
            content=db_row.content,  # type: ignore
            is_public=db_row.is_public,  # type: ignore
            created_at=db_row.created_at,  # type: ignore
            updated_at=db_row.updated_at,  # type: ignore
            count_like=db_row.count_like,  # type: ignore
            count_view=db_row.count_view,  # type: ignore
            tags={
                Tag(tag_id=tag["tag_id"], tag_name=tag["tag_name"])
                for tag in db_row.tags  # type: ignore
            },
        )

    assert created_cheatsheet == expected_result
