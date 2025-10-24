from datetime import datetime
from uuid import UUID

from src.domain.entities import Cheatsheet, Tag


def test_update_partial_fields():
    original_cheatsheet = Cheatsheet(
        cheatsheet_id=UUID("01998b2f-af53-7ca0-85f3-9c01093dd430"),
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
        "tags": {Tag(3, "Algorithms")},
    }

    expected_result = Cheatsheet(
        **update_fields,
        cheatsheet_id=original_cheatsheet.cheatsheet_id,
        created_at=original_cheatsheet.created_at,
        updated_at=original_cheatsheet.updated_at,
        count_like=original_cheatsheet.count_like,
        count_view=original_cheatsheet.count_view,
    )

    updated_cheatsheet = original_cheatsheet.update(update_fields)

    assert updated_cheatsheet == expected_result
