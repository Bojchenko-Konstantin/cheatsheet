from datetime import datetime
from typing import Self
from uuid import UUID

import pytest

from application.interfaces.repositories.cheatsheet import ICheatsheetRepo
from application.interfaces.unit_of_work import IUnitOfWork
from application.use_cases.cheatsheet import CheatsheetUseCase
from domain.entities import Cheatsheet, Tag


class FakeCheatsheetRepo(ICheatsheetRepo):
    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        return Cheatsheet(
            cheatsheet_id=cheatsheet_id,
            title="title",
            content="content",
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
            is_public=True,
            tags={Tag(1, "Tag_1")},
            count_like=10,
            count_view=10,
        )

    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        pass


class FakeUnitOfWork(IUnitOfWork):
    async def __aenter__(self) -> Self:
        self.cheatsheet_repo: ICheatsheetRepo = FakeCheatsheetRepo()
        return await super().__aenter__()

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass


@pytest.mark.asyncio
class TestCheatsheetUseCase:
    async def test_get_cheatsheet_when_id_exist(self):
        unit_of_work = FakeUnitOfWork()
        sut = CheatsheetUseCase(unit_of_work)
        existing_id = 1
        expected_result = Cheatsheet(
            cheatsheet_id=existing_id,
            title="title",
            content="content",
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
            is_public=True,
            tags={Tag(1, "Tag_1")},
            count_like=10,
            count_view=10,
        )

        cheatsheet = await sut.get_by_id(1)

        assert cheatsheet == expected_result
