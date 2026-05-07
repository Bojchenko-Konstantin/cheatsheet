from datetime import datetime
from uuid import UUID

import pytest

from src.domain.entities import Cheatsheet, CheatsheetStats, Tag
from src.domain.exceptions import (
    CheatsheetAccessDeniedError,
    CheatsheetModificationDeniedError,
    InvalidCheatsheetContentError,
    InvalidCheatsheetTitleError,
    NegativeStatsError,
    TagLimitExceededError,
)

OWNER_ID = UUID("019b4a71-173e-7f64-a840-9e8b042658cd")
STRANGER_ID = UUID("019b4a71-173e-7f64-a840-9e8b042658ce")
CHEATSHEET_ID = UUID("01998b2f-af53-7ca0-85f3-9c01093dd430")
TITLE = "Test Cheatsheet"
CONTENT = "Test content"


@pytest.mark.parametrize(
    "test_data, data_for_expected_result",
    [
        (
            {
                "cheatsheet_id": CHEATSHEET_ID,
                "user_id": OWNER_ID,
                "title": TITLE,
                "content": CONTENT,
                "is_public": True,
                "tags": [
                    {"tag_id": 1, "tag_name": "Python"},
                    {"tag_id": 2, "tag_name": "Testing"},
                ],
                "created_at": datetime(2025, 1, 1),
                "updated_at": datetime(2025, 1, 1),
                "count_like": 5,
                "count_view": 10,
            },
            {
                "stats": CheatsheetStats(count_like=5, count_view=10),
            },
        ),
        (
            {
                "cheatsheet_id": UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
                "user_id": str(OWNER_ID),
                "title": TITLE,
                "content": CONTENT,
                "is_public": True,
                "tags": [],
                "created_at": datetime(2025, 1, 1),
                "updated_at": datetime(2025, 1, 1),
                "count_like": 0,
                "count_view": 0,
            },
            {
                "tags": set(),
            },
        ),
    ],
)
def test_cheatsheet_creation_from_dict_was_successful(
    test_data: dict, data_for_expected_result: dict
):
    created_cheatsheet = Cheatsheet.from_dict(test_data)
    expected_result = _make_cheatsheet(**data_for_expected_result)

    assert created_cheatsheet == expected_result


def test_private_cheatsheet_accessible_by_owner_was_successful():
    cheatsheet = _make_cheatsheet(is_public=False)

    assert cheatsheet.is_accessible_by(OWNER_ID) is True


def test_private_cheatsheet_access_by_stranger_was_denied():
    cheatsheet = _make_cheatsheet(is_public=False)

    assert cheatsheet.is_accessible_by(STRANGER_ID) is False


def test_private_cheatsheet_access_by_anonymous_was_denied():
    cheatsheet = _make_cheatsheet(is_public=False)

    assert cheatsheet.is_accessible_by(None) is False


def test_public_cheatsheet_access_by_stranger_was_successful():
    cheatsheet = _make_cheatsheet()

    assert cheatsheet.is_accessible_by(STRANGER_ID) is True


def test_public_cheatsheet_access_by_anonymous_was_successful():
    cheatsheet = _make_cheatsheet()

    assert cheatsheet.is_accessible_by(None) is True


def test_ensure_accessible_by_for_stranger_was_denied():
    cheatsheet = _make_cheatsheet(is_public=False)

    with pytest.raises(CheatsheetAccessDeniedError):
        cheatsheet.ensure_accessible_by(STRANGER_ID)


def test_ensure_accessible_by_for_owner_was_successful():
    cheatsheet = _make_cheatsheet(is_public=False)

    cheatsheet.ensure_accessible_by(OWNER_ID)


def test_ensure_owned_by_for_non_owner_was_denied():
    cheatsheet = _make_cheatsheet()

    with pytest.raises(CheatsheetModificationDeniedError):
        cheatsheet.ensure_is_owner(STRANGER_ID)


def test_ensure_is_owner_for_owner_was_successful():
    cheatsheet = _make_cheatsheet()

    cheatsheet.ensure_is_owner(OWNER_ID)


@pytest.mark.parametrize("count_like, count_view", [(-1, 0), (0, -1)])
def test_cheatsheet_stats_creation_with_negative_stats_count_was_denied(
    count_like: int, count_view: int
):
    with pytest.raises(NegativeStatsError):
        CheatsheetStats(count_like=count_like, count_view=count_view)


@pytest.mark.parametrize("title", ["ab", "a" * 51])
def test_cheatsheet_title_with_forbidden_symbol_amount_was_denied(title: str):
    with pytest.raises(InvalidCheatsheetTitleError):
        _make_cheatsheet(title=title)


@pytest.mark.parametrize("content", ["", "   "])
def test_cheatsheet_with_improper_content_was_denied(content: str):
    with pytest.raises(InvalidCheatsheetContentError):
        _make_cheatsheet(content=content)


def test_cheatsheet_max_tags_allowed_was_successful():
    _make_cheatsheet(
        tags={Tag(i, f"tag_{i}") for i in range(1, 7)},
    )


def test_cheatsheet_too_many_tags_was_denied():
    with pytest.raises(TagLimitExceededError):
        _make_cheatsheet(
            tags={Tag(i, f"tag_{i}") for i in range(1, 8)},
        )


def _make_cheatsheet(
    *,
    is_public: bool = True,
    title: str = TITLE,
    content: str = CONTENT,
    tags: set[Tag] | None = None,
    stats: CheatsheetStats = CheatsheetStats(),
) -> Cheatsheet:
    if tags is None:
        tags = {Tag(1, "Python"), Tag(2, "Testing")}

    return Cheatsheet(
        cheatsheet_id=CHEATSHEET_ID,
        user_id=OWNER_ID,
        title=title,
        content=content,
        is_public=is_public,
        tags=tags,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
        stats=stats,
    )
