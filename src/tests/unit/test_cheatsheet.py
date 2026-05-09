from datetime import datetime
from typing import Any, Self
from uuid import UUID

import pytest

from src.application.dto import (
    CheatsheetList,
    CheatsheetSearchSuggestions,
    PaginationMetadata,
)
from src.application.interfaces import ICheatsheetRepo, IUnitOfWork
from src.application.interfaces.services import CursorDTO, ICheatsheetSearchService
from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import Cheatsheet, CheatsheetStats, Tag


class FakeCheatsheetRepo(ICheatsheetRepo):
    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        return Cheatsheet(
            cheatsheet_id=cheatsheet_id,
            title="title",
            content="content",
            user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
            is_public=True,
            tags={Tag(1, "Tag_1")},
            stats=CheatsheetStats(count_like=10, count_view=10),
        )

    async def create(self, create_data: dict[str, Any]) -> Cheatsheet:
        updated_data = dict(
            cheatsheet_id=UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
        )

        created_cheatsheet = Cheatsheet.from_dict(dict(**updated_data, **create_data))
        return created_cheatsheet

    async def update(self, update_data: dict[str, Any]) -> Cheatsheet:
        return Cheatsheet.from_dict(
            dict(
                **update_data,
                user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
                created_at=datetime(2025, 1, 1),
                updated_at=datetime(2025, 1, 2),
            )
        )

    async def list_accessible_cheatsheets(
        self,
        user_id: UUID | None,
        cursor: str | None,
        size: int,
        tag: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
    ) -> CheatsheetList:
        raise NotImplementedError

    async def search_suggestions(
        self, query: str, limit: int
    ) -> CheatsheetSearchSuggestions:
        raise NotImplementedError


class FakeSearchService(ICheatsheetSearchService):
    @property
    def similarity_search_threshold(self) -> float:
        return 0.2

    @property
    def similarity_suggestions_threshold(self) -> float:
        return 0.2

    def validate_search_query(self, query: str | None) -> None:
        pass

    def validate_sort_params(self, sort_by: str, sort_order: str) -> None:
        pass

    def decode_cursor(self, cursor_str: str | None) -> CursorDTO | None:
        return None

    def build_pagination_metadata(
        self,
        rows: list,
        size: int,
        current_cursor: str | None,
        sort_by: str,
    ) -> PaginationMetadata:
        return PaginationMetadata(
            next_cursor=None,
            previous_cursor=None,
            has_next=False,
            has_previous=False,
        )

    def validate_suggestions_limit(self, limit: int) -> None:
        pass


class FakeUnitOfWork(IUnitOfWork):
    async def __aenter__(self) -> Self:
        self.cheatsheet_repo: ICheatsheetRepo = FakeCheatsheetRepo()
        return await super().__aenter__()

    def readonly(self) -> Any:
        return self

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_get_cheatsheet_by_id_was_successful():
    unit_of_work = FakeUnitOfWork()
    search_service = FakeSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    existing_id = UUID("01998b2f-af53-7ca0-85f3-9c01093dd430")
    expected_result = Cheatsheet(
        cheatsheet_id=existing_id,
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        title="title",
        content="content",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
        is_public=True,
        tags={Tag(1, "Tag_1")},
        stats=CheatsheetStats(count_like=10, count_view=10),
    )

    cheatsheet = await sut.get_by_id(existing_id)

    assert cheatsheet == expected_result


@pytest.mark.asyncio
async def test_create_cheatsheet_was_successful():
    unit_of_work = FakeUnitOfWork()
    search_service = FakeSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    create_data = dict(
        title="title",
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        content="content",
        is_public=True,
        tags=[
            {"tag_id": 1, "tag_name": "Python"},
            {"tag_id": 2, "tag_name": "Testing"},
        ],
    )

    generated_fields = {
        "cheatsheet_id": UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
        "created_at": datetime(2025, 1, 1),
        "updated_at": datetime(2025, 1, 1),
    }

    expected_result = Cheatsheet(
        title="title",
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        content="content",
        is_public=True,
        tags={Tag(1, "Python"), Tag(2, "Testing")},
        stats=CheatsheetStats(count_like=0, count_view=0),
        **generated_fields,
    )

    created_cheatsheet = await sut.create(create_data)

    assert created_cheatsheet == expected_result


@pytest.mark.asyncio
async def test_cheatsheet_was_updated_and_timestamps_preserved():
    unit_of_work = FakeUnitOfWork()
    search_service = FakeSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    existing_id = UUID("01998b2f-af53-7ca0-85f3-9c01093dd430")

    expected_result = Cheatsheet(
        cheatsheet_id=existing_id,
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        title="Updated Title",
        content="Updated Content",
        is_public=False,
        tags={Tag(3, "Updated_Tag"), Tag(4, "New_Tag")},
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 2),
        stats=CheatsheetStats(count_like=0, count_view=0),
    )

    update_data = dict(
        cheatsheet_id=existing_id,
        title="Updated Title",
        content="Updated Content",
        is_public=False,
        tags=[
            {"tag_id": 3, "tag_name": "Updated_Tag"},
            {"tag_id": 4, "tag_name": "New_Tag"},
        ],
    )

    updated_cheatsheet = await sut.update(update_data)

    assert updated_cheatsheet == expected_result


@pytest.mark.asyncio
async def test_tag_conversion_from_dict_to_objects_was_successful():
    unit_of_work = FakeUnitOfWork()
    search_service = FakeSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    existing_id = UUID("01998b2f-af53-7ca0-85f3-9c01093dd430")

    expected_result = Cheatsheet(
        cheatsheet_id=existing_id,
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        title="Updated Title",
        content="Updated Content",
        is_public=True,
        tags={Tag(1, "Python"), Tag(2, "Testing")},
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 2),
        stats=CheatsheetStats(count_like=0, count_view=0),
    )

    update_data = dict(
        cheatsheet_id=existing_id,
        title="Updated Title",
        content="Updated Content",
        is_public=True,
        tags=[
            {"tag_id": 1, "tag_name": "Python"},
            {"tag_id": 2, "tag_name": "Testing"},
        ],
    )

    updated_cheatsheet = await sut.update(update_data)

    assert updated_cheatsheet == expected_result
