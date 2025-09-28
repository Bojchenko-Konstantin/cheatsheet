"""create uuid v7 function

Revision ID: 77b6e2e41c37
Revises: 3434ab130e52
Create Date: 2025-09-27 15:52:18.268617

"""

from pathlib import Path
from typing import Sequence, Union

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "77b6e2e41c37"
down_revision: Union[str, None] = "3434ab130e52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_v7_functions = (
    Path(
        context.config.get_section_option(  # type: ignore
            "extra",
            "functions.dir",
        )
    )
    / "uuid_v7"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        (uuid_v7_functions / "upgrade.sql").read_text(),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        (uuid_v7_functions / "downgrade.sql").read_text(),
    )
