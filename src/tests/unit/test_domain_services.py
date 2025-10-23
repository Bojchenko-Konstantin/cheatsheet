from datetime import datetime
from uuid import UUID

from src.domain.entities import Cheatsheet, Tag


class TestCheatsheetDomainServices:
    def test_update_partial_fields(self):
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

        updated_cheatsheet = original_cheatsheet.update(
            {
                "title": "Updated Title",
                "content": "Updated Content",
                "is_public": False,
            }
        )

        expected_result = Cheatsheet(
            cheatsheet_id=original_cheatsheet.cheatsheet_id,
            title="Updated Title",
            content="Updated Content",
            is_public=False,
            tags=original_cheatsheet.tags,
            created_at=original_cheatsheet.created_at,
            updated_at=original_cheatsheet.updated_at,
            count_like=original_cheatsheet.count_like,
            count_view=original_cheatsheet.count_view,
        )

        assert updated_cheatsheet == expected_result
