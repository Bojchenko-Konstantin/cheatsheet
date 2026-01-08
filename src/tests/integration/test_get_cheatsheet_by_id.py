from datetime import datetime
from uuid import UUID

import pytest

from src.application.exceptions import CheatsheetNotFoundError
from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import Cheatsheet, Tag
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_cheathsheet_by_id(populate_db_for_single_cheatsheet):
    unit_of_work = SQLAlchemyUnitOfWork()
    cheatsheet_id, user_id, raw_tags = populate_db_for_single_cheatsheet
    tags = {Tag(tag_id=tag["tag_id"], tag_name=tag["tag_name"]) for tag in raw_tags}
    sut = CheatsheetUseCase(unit_of_work)
    expected_result = Cheatsheet(
        cheatsheet_id=cheatsheet_id,
        user_id=user_id,
        title="title_1",
        content="content_1",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
        is_public=False,
        tags=tags,
        count_like=1,
        count_view=1,
    )

    cheatsheet = await sut.get_by_id(cheatsheet_id, current_user_id=user_id)

    assert cheatsheet == expected_result


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_get_non_existent_cheathsheet_by_id_raises_error():
    unit_of_work = SQLAlchemyUnitOfWork()
    sut = CheatsheetUseCase(unit_of_work)
    non_existent_cheatsheet_id = UUID("01998b2f-af53-7ca0-85f3-9c01093dd430")

    with pytest.raises(CheatsheetNotFoundError):
        await sut.get_by_id(non_existent_cheatsheet_id)
