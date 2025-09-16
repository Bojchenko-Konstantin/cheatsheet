from datetime import datetime

import pytest

from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import Cheatsheet, Tag
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_cheathsheet_by_id(populate_db_for_single_cheatsheet):
    unit_of_work = SQLAlchemyUnitOfWork()
    cheatsheet_id, raw_tags = populate_db_for_single_cheatsheet
    tags = {Tag(tag_id, tag_name) for tag_id, tag_name in raw_tags}
    sut = CheatsheetUseCase(unit_of_work)
    expected_result = Cheatsheet(
        cheatsheet_id=cheatsheet_id,
        title="title_1",
        content="content_1",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
        is_public=False,
        tags=tags,
        count_like=1,
        count_view=1,
    )

    cheatsheet = await sut.get_by_id(cheatsheet_id)

    assert cheatsheet == expected_result
