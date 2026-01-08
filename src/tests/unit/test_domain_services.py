from datetime import datetime
from uuid import UUID

from src.domain.entities import Cheatsheet, Tag


def test_update_partial_fields():
    original_cheatsheet = Cheatsheet(
        cheatsheet_id=UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
        user_id=UUID("019b4a71-173e-7f64-a840-9e8b042658cd"),
        title="Original Title",
        content="Original Content",
        is_public=True,
        tags={Tag(1, "Python"), Tag(2, "Testing")},
        created_at=datetime.now(),
        updated_at=datetime.now(),
        count_like=5,
        count_view=10,
    )

    update_fields = {
        "title": "Updated Title",
        "content": "Updated Content",
        "is_public": False,
        "tags": [{"tag_id": 3, "tag_name": "Algorithms"}],
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
        count_like=original_cheatsheet.count_like,
        count_view=original_cheatsheet.count_view,
    )

    updated_cheatsheet = original_cheatsheet.update(update_fields)

    assert updated_cheatsheet == expected_result


def test_from_dict():
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
        **{**test_data, "tags": {Tag(**tag) for tag in raw_tags_data}}
    )

    created_cheatsheet = Cheatsheet.from_dict(test_data)

    assert created_cheatsheet == expected_result
