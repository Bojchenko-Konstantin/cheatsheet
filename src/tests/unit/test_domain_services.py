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


def test_cheatsheet_partial_update_was_successful():
    original_cheatsheet = Cheatsheet(
        cheatsheet_id=UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        title="Original Title",
        content="Original Content",
        is_public=True,
        tags={Tag(1, "Python"), Tag(2, "Testing")},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        stats=CheatsheetStats(count_like=5, count_view=10),
    )

    update_fields = {
        "title": "Updated Title",
        "content": "Updated Content",
        "is_public": False,
        "tags": {Tag(3, "Algorithms")},
    }

    expected_result = Cheatsheet(
        cheatsheet_id=original_cheatsheet.cheatsheet_id,
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        title="Updated Title",
        content="Updated Content",
        is_public=False,
        tags={Tag(3, "Algorithms")},
        created_at=original_cheatsheet.created_at,
        updated_at=original_cheatsheet.updated_at,
        stats=CheatsheetStats(count_like=5, count_view=10),
    )

    updated_cheatsheet = original_cheatsheet.update(**update_fields)

    assert updated_cheatsheet == expected_result


def test_cheatsheet_creation_from_dict_was_successful():
    raw_tags_data = [
        {"tag_id": 1, "tag_name": "Python"},
        {"tag_id": 2, "tag_name": "Testing"},
    ]

    test_data = {
        "cheatsheet_id": UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
        "user_id": UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        "title": "Test Cheatsheet",
        "content": "Test content",
        "is_public": True,
        "tags": raw_tags_data,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "count_like": 5,
        "count_view": 10,
    }

    expected_result = Cheatsheet(
        cheatsheet_id=test_data["cheatsheet_id"],
        user_id=test_data["user_id"],
        title=test_data["title"],
        content=test_data["content"],
        is_public=test_data["is_public"],
        tags={Tag(**tag) for tag in raw_tags_data},
        created_at=test_data["created_at"],
        updated_at=test_data["updated_at"],
        stats=CheatsheetStats(
            count_like=test_data["count_like"],
            count_view=test_data["count_view"],
        ),
    )

    created_cheatsheet = Cheatsheet.from_dict(test_data)

    assert created_cheatsheet == expected_result


def test_cheatsheet_from_dict_with_string_user_id_was_successful():
    test_data = {
        "cheatsheet_id": UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
        "user_id": str(OWNER_ID),
        "title": "Test Cheatsheet",
        "content": "Test content",
        "is_public": True,
        "tags": [],
        "created_at": datetime(2025, 1, 1),
        "updated_at": datetime(2025, 1, 1),
        "count_like": 0,
        "count_view": 0,
    }

    expected_result = _make_cheatsheet(
        is_public=True,
        title="Test Cheatsheet",
        content="Test content",
        tags=set(),
    )

    converted_cheatsheet = Cheatsheet.from_dict(test_data)

    assert converted_cheatsheet == expected_result


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
    cheatsheet = _make_cheatsheet(is_public=True)

    assert cheatsheet.is_accessible_by(STRANGER_ID) is True


def test_public_cheatsheet_access_by_anonymous_was_successful():
    cheatsheet = _make_cheatsheet(is_public=True)

    assert cheatsheet.is_accessible_by(None) is True


def test_ensure_accessible_by_for_stranger_was_denied():
    cheatsheet = _make_cheatsheet(is_public=False)

    with pytest.raises(CheatsheetAccessDeniedError):
        cheatsheet.ensure_accessible_by(STRANGER_ID)


def test_ensure_accessible_by_for_owner_was_successful():
    cheatsheet = _make_cheatsheet(is_public=False)

    cheatsheet.ensure_accessible_by(OWNER_ID)


def test_ensure_owned_by_for_non_owner_was_denied():
    cheatsheet = _make_cheatsheet(is_public=True)

    with pytest.raises(CheatsheetModificationDeniedError):
        cheatsheet.ensure_is_owner(STRANGER_ID)


def test_ensure_owned_by_for_owner_was_successful():
    cheatsheet = _make_cheatsheet(is_public=True)

    cheatsheet.ensure_is_owner(OWNER_ID)


def test_cheatsheet_stats_creation_with_negative_like_count_was_denied():
    with pytest.raises(NegativeStatsError):
        CheatsheetStats(count_like=-1, count_view=0)


def test_cheatsheet_stats_creation_with_negative_view_count_was_denied():
    with pytest.raises(NegativeStatsError):
        CheatsheetStats(count_like=0, count_view=-1)


def test_cheatsheet_title_too_short_was_denied():
    with pytest.raises(InvalidCheatsheetTitleError):
        _make_cheatsheet(is_public=True, title="ab")


def test_cheatsheet_title_too_long_was_denied():
    with pytest.raises(InvalidCheatsheetTitleError):
        _make_cheatsheet(is_public=True, title="a" * 51)


def test_cheatsheet_content_empty_was_denied():
    with pytest.raises(InvalidCheatsheetContentError):
        _make_cheatsheet(is_public=True, content="")


def test_cheatsheet_content_whitespace_only_was_denied():
    with pytest.raises(InvalidCheatsheetContentError):
        _make_cheatsheet(is_public=True, content="   ")


def test_cheatsheet_too_many_tags_was_denied():
    with pytest.raises(TagLimitExceededError):
        _make_cheatsheet(
            is_public=True,
            tags={Tag(i, f"tag_{i}") for i in range(1, 8)},
        )


def test_cheatsheet_max_tags_allowed_was_successful():
    _make_cheatsheet(
        is_public=True,
        tags={Tag(i, f"tag_{i}") for i in range(1, 7)},
    )


def _make_cheatsheet(
    *,
    is_public: bool,
    title: str = "Test Title",
    content: str = "Test content",
    tags: set[Tag] | None = None,
    stats: CheatsheetStats | None = None,
) -> Cheatsheet:
    if tags is None:
        tags = {Tag(1, "Python"), Tag(2, "Testing")}
    if stats is None:
        stats = CheatsheetStats(count_like=0, count_view=0)

    return Cheatsheet(
        cheatsheet_id=UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
        user_id=OWNER_ID,
        title=title,
        content=content,
        is_public=is_public,
        tags=tags,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
        stats=stats,
    )
