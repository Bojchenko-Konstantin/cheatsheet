import contextlib
from datetime import datetime
from typing import Any
from uuid import UUID

import pytest

from src.application.dto import (
    CheatsheetList,
    CheatsheetSearchSuggestions,
    PaginationMetadata,
)
from src.application.exceptions import (
    InvalidSearchQueryError,
    InvalidSortFieldError,
    InvalidSortOrderError,
)
from src.application.interfaces import ICheatsheetRepo, IUnitOfWork
from src.application.interfaces.services import CursorDTO, ICheatsheetSearchService
from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import (
    Cheatsheet,
    CheatsheetStats,
    Tag,
)
from src.infrastructure.services import CursorService


class FakeCursorService(CursorService):
    @staticmethod
    def encode(entity_id: UUID, sort_value: datetime | str | int) -> str:
        clean_id = str(entity_id).replace("-", "")
        if isinstance(sort_value, datetime):
            sort_str = str(int(sort_value.timestamp()))
        else:
            sort_str = str(sort_value)
        return f"{clean_id}_{sort_str}"

    @staticmethod
    def decode(cursor: str):
        from src.application.exceptions import InvalidCursorError
        from src.infrastructure.services.cursor_service import Cursor

        try:
            id_hex, sort_value = cursor.split("_", 1)
            entity_id = UUID(hex=id_hex)
        except (ValueError, AttributeError) as e:
            raise InvalidCursorError from e
        with contextlib.suppress(ValueError, OSError, TypeError):
            sort_value = datetime.fromtimestamp(int(sort_value))

        return Cursor(entity_id=entity_id, sort_value=sort_value)


class FakeCheatsheetSearchService(ICheatsheetSearchService):
    def __init__(self) -> None:
        self._cursor_service = CursorService()

    @property
    def similarity_search_threshold(self) -> float:
        return 0.2

    @property
    def similarity_suggestions_threshold(self) -> float:
        return 0.2

    def validate_search_query(self, query: str | None) -> None:
        if query is not None and len(query.strip()) < 2:
            raise InvalidSearchQueryError

    def validate_sort_params(self, sort_by: str, sort_order: str) -> None:
        if sort_by not in ("created_at", "updated_at", "title"):
            raise InvalidSortFieldError
        if sort_order not in ("asc", "desc"):
            raise InvalidSortOrderError

    def validate_suggestions_limit(self, limit: int) -> None:
        if limit > 10:
            raise InvalidSearchQueryError

    def decode_cursor(self, cursor_str: str | None) -> CursorDTO | None:
        if cursor_str is None:
            return None
        cursor = self._cursor_service.decode(cursor_str)
        return CursorDTO(
            entity_id=cursor.entity_id,
            sort_value=cursor.sort_value,
        )

    def build_pagination_metadata(
        self,
        rows: list,
        size: int,
        current_cursor: str | None,
        sort_by: str,
    ) -> PaginationMetadata:
        has_next = len(rows) > size
        has_previous = current_cursor is not None
        items = rows[:size]

        next_cursor = None
        previous_cursor = None

        if has_next and items:
            last = items[-1]
            next_cursor = self._cursor_service.encode(
                last.cheatsheet_id,
                getattr(last, sort_by),
            )

        if has_previous and items:
            first = items[0]
            previous_cursor = self._cursor_service.encode(
                first.cheatsheet_id,
                getattr(first, sort_by),
            )

        return PaginationMetadata(
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
            has_next=has_next,
            has_previous=has_previous,
        )


class FakeCheatsheetRepoForList(ICheatsheetRepo):
    def __init__(self) -> None:
        self._items = [
            Cheatsheet(
                cheatsheet_id=UUID("019dfc6d-b685-720a-8b90-a1832416676d"),
                user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
                title="PostgreSQL Guide",
                content="Database tips",
                is_public=True,
                created_at=datetime(2026, 5, 6, 12, 0, 2),
                updated_at=datetime(2026, 5, 6, 12, 0, 2),
                tags={Tag(3, "postgresql")},
                stats=CheatsheetStats(),
            ),
            Cheatsheet(
                cheatsheet_id=UUID("019dfc6d-b685-720a-8b90-a1832416676c"),
                user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
                title="FastAPI Tutorial",
                content="Building APIs",
                is_public=True,
                created_at=datetime(2026, 5, 6, 12, 0, 1),
                updated_at=datetime(2026, 5, 6, 12, 0, 1),
                tags={Tag(2, "fastapi")},
                stats=CheatsheetStats(),
            ),
            Cheatsheet(
                cheatsheet_id=UUID("019dfc6d-b685-720a-8b90-a1832416676b"),
                user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
                title="Python Basics",
                content="Python fundamentals",
                is_public=True,
                created_at=datetime(2026, 5, 6, 12, 0, 0),
                updated_at=datetime(2026, 5, 6, 12, 0, 0),
                tags={Tag(1, "python")},
                stats=CheatsheetStats(),
            ),
            Cheatsheet(
                cheatsheet_id=UUID("019dfc6d-b685-720a-8b90-a1832416676e"),
                user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
                title="Django Web Framework",
                content="Django basics",
                is_public=True,
                created_at=datetime(2026, 5, 6, 12, 0, 4),
                updated_at=datetime(2026, 5, 6, 12, 0, 4),
                tags={Tag(4, "django")},
                stats=CheatsheetStats(),
            ),
        ]

    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        raise NotImplementedError

    async def create(self, create_data: dict[str, Any]) -> Cheatsheet:
        raise NotImplementedError

    async def update(self, update_data: dict[str, Any]) -> Cheatsheet:
        raise NotImplementedError

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
        items = list(self._items)

        if search:
            items = [c for c in items if search.lower() in c.title.lower()]
        if tag:
            items = [
                c
                for c in items
                if any(t.tag_name and t.tag_name == tag for t in c.tags)
            ]

        reverse = sort_order == "desc"
        items = sorted(items, key=lambda x: getattr(x, sort_by), reverse=reverse)

        if cursor:
            items = self._skip_before_cursor(items, cursor)

        search_service = FakeCheatsheetSearchService()
        pagination = search_service.build_pagination_metadata(
            rows=items,
            size=size,
            current_cursor=cursor,
            sort_by=sort_by,
        )

        result_items = items[:size]

        return CheatsheetList(
            items=result_items,
            next_cursor=pagination.next_cursor,
            previous_cursor=pagination.previous_cursor,
            has_next=pagination.has_next,
            has_previous=pagination.has_previous,
        )

    async def search_suggestions(
        self,
        query: str,
        limit: int,
    ) -> CheatsheetSearchSuggestions:
        return CheatsheetSearchSuggestions(
            titles=self._matching_titles(query, limit),
            tags=self._matching_tags(query, limit),
        )

    def _skip_before_cursor(
        self, items: list[Cheatsheet], cursor: str
    ) -> list[Cheatsheet]:
        try:
            id_hex = cursor.split("_")[0]
            cursor_id = UUID(hex=id_hex)
        except (ValueError, AttributeError):
            return items

        for i, c in enumerate(items):
            if c.cheatsheet_id == cursor_id:
                return items[i + 1 :]
        return items

    def _matching_titles(self, query: str, limit: int) -> list[str]:
        return [c.title for c in self._items if query.lower() in c.title.lower()][
            :limit
        ]

    def _matching_tags(self, query: str, limit: int) -> list[str]:
        matching: list[str] = []
        for c in self._items:
            for t in c.tags:
                if (
                    t.tag_name
                    and query.lower() in t.tag_name.lower()
                    and t.tag_name not in matching
                ):
                    matching.append(t.tag_name)
        return matching[:limit]


class FakeUnitOfWorkForList(IUnitOfWork):
    def __init__(self) -> None:
        self._cheatsheet_repo = FakeCheatsheetRepoForList()

    def readonly(self) -> "FakeUnitOfWorkForList":
        return self

    async def __aenter__(self) -> "FakeUnitOfWorkForList":
        self.cheatsheet_repo: ICheatsheetRepo = self._cheatsheet_repo
        self.user_repo = None  # type: ignore[assignment]
        self.token_repo = None  # type: ignore[assignment]
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_get_cheatsheet_list_first_page_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=2,
        tag=None,
        search=None,
        sort_by="created_at",
        sort_order="desc",
    )

    titles = [item.title for item in cheatsheet_list.items]

    assert titles == ["Django Web Framework", "PostgreSQL Guide"]
    assert cheatsheet_list.has_next is True
    assert cheatsheet_list.has_previous is False
    assert cheatsheet_list.next_cursor is not None
    assert cheatsheet_list.previous_cursor is None


@pytest.mark.asyncio
async def test_get_cheatsheet_list_last_page_has_no_next():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=10,
        tag=None,
        search=None,
        sort_by="created_at",
        sort_order="desc",
    )

    assert cheatsheet_list.has_next is False
    assert cheatsheet_list.next_cursor is None
    assert cheatsheet_list.has_previous is False
    assert len(cheatsheet_list.items) == 4


@pytest.mark.asyncio
async def test_get_cheatsheet_list_with_search_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=10,
        tag=None,
        search="python",
        sort_by="created_at",
        sort_order="desc",
    )

    assert len(cheatsheet_list.items) == 1
    assert cheatsheet_list.items[0].title == "Python Basics"
    assert cheatsheet_list.has_next is False
    assert cheatsheet_list.has_previous is False


@pytest.mark.asyncio
async def test_get_cheatsheet_list_with_tag_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=10,
        tag="fastapi",
        search=None,
        sort_by="created_at",
        sort_order="desc",
    )

    assert len(cheatsheet_list.items) == 1
    assert cheatsheet_list.items[0].title == "FastAPI Tutorial"
    assert cheatsheet_list.has_next is False
    assert cheatsheet_list.has_previous is False


@pytest.mark.asyncio
async def test_get_search_suggestions_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    suggestions = await sut.get_search_suggestions(query="py", limit=5)

    assert suggestions.titles == ["Python Basics"]
    assert suggestions.tags == ["python"]


@pytest.mark.asyncio
async def test_get_search_suggestions_no_results():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    suggestions = await sut.get_search_suggestions(query="xyz", limit=5)

    assert suggestions.titles == []
    assert suggestions.tags == []


@pytest.mark.asyncio
async def test_get_cheatsheet_list_sorting_desc_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=10,
        tag=None,
        search=None,
        sort_by="created_at",
        sort_order="desc",
    )

    titles = [item.title for item in cheatsheet_list.items]

    assert titles == [
        "Django Web Framework",
        "PostgreSQL Guide",
        "FastAPI Tutorial",
        "Python Basics",
    ]


@pytest.mark.asyncio
async def test_get_cheatsheet_list_sorting_by_title_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=10,
        tag=None,
        search=None,
        sort_by="title",
        sort_order="asc",
    )

    titles = [item.title for item in cheatsheet_list.items]

    assert titles == sorted(titles)
    assert titles[0] == "Django Web Framework"
    assert titles[-1] == "Python Basics"


@pytest.mark.asyncio
async def test_get_cheatsheet_list_with_search_and_tag_combined_was_successful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    cheatsheet_list = await sut.get_cheatsheet_list(
        user_id=None,
        cursor=None,
        size=10,
        tag="python",
        search="python",
        sort_by="created_at",
        sort_order="desc",
    )

    assert len(cheatsheet_list.items) == 1
    assert cheatsheet_list.items[0].title == "Python Basics"


@pytest.mark.asyncio
async def test_get_cheatsheet_list_with_invalid_sort_field_was_unsuccessful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    with pytest.raises(InvalidSortFieldError):
        await sut.get_cheatsheet_list(
            user_id=None,
            cursor=None,
            size=10,
            tag=None,
            search=None,
            sort_by="invalid_field",
            sort_order="asc",
        )


@pytest.mark.asyncio
async def test_get_cheatsheet_list_with_invalid_sort_order_was_unsuccessful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    with pytest.raises(InvalidSortOrderError):
        await sut.get_cheatsheet_list(
            user_id=None,
            cursor=None,
            size=10,
            tag=None,
            search=None,
            sort_by="created_at",
            sort_order="invalid",
        )


@pytest.mark.asyncio
async def test_get_search_suggestions_with_invalid_limit_was_unsuccessful():
    unit_of_work = FakeUnitOfWorkForList()
    search_service = FakeCheatsheetSearchService()
    sut = CheatsheetUseCase(unit_of_work, search_service)

    with pytest.raises(InvalidSearchQueryError):
        await sut.get_search_suggestions(query="py", limit=11)
