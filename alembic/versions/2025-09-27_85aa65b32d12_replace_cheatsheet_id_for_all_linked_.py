"""replace cheatsheet_id for all linked tables

Revision ID: 85aa65b32d12
Revises: 90c3fa402a2e
Create Date: 2025-09-27 17:18:40.875758

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "85aa65b32d12"
down_revision: Union[str, None] = "90c3fa402a2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "cheatsheet_stats",
        "cheatsheet_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.alter_column(
        "cheatsheet_to_tag",
        "cheatsheet_id",
        existing_type=sa.UUID(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "cheatsheet_to_tag",
        "cheatsheet_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.alter_column(
        "cheatsheet_stats",
        "cheatsheet_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
