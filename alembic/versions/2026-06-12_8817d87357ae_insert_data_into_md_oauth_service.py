"""Insert data into md_oauth_service

Revision ID: 8817d87357ae
Revises: 7ad809af1b3f
Create Date: 2026-06-12 16:01:10.604019

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8817d87357ae"
down_revision: Union[str, None] = "7ad809af1b3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    conn.execute(
        sa.text("INSERT INTO md_oauth_service(oauth_service_name) VALUES (:value)"),
        [{"value": "yandex"}, {"value": "github"}],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        "DELETE FROM md_oauth_service WHERE oauth_service_name IN ('yandex', 'github')"
    )
