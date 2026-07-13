"""Add google to md_oauth_service table

Revision ID: cd90a3da066c
Revises: 4602d7b5d589
Create Date: 2026-07-13 22:40:16.617907

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cd90a3da066c"
down_revision: Union[str, None] = "4602d7b5d589"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    conn.execute(
        sa.text("INSERT INTO md_oauth_service(oauth_service_name) VALUES (:value)"),
        [{"value": "google"}],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DELETE FROM md_oauth_service WHERE oauth_service_name = 'google'")
