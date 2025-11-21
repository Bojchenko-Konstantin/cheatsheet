"""fix: populate_md_refresh_token_status

Revision ID: 1c903d27104e
Revises: fb1e2a7a4788
Create Date: 2025-11-21 22:32:22.645767

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c903d27104e"
down_revision: Union[str, None] = "fb1e2a7a4788"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("SELECT setval('md_refresh_token_status_status_id_seq', 1, false)")

    op.execute(
        """
        INSERT INTO md_refresh_token_status (status_name) VALUES
        ('active'),
        ('expired'),
        ('revoked')
        """
    )


def downgrade():
    op.execute(
        """DELETE FROM md_refresh_token_status
        WHERE status_name IN ('active', 'expired', 'revoked')"""
    )
