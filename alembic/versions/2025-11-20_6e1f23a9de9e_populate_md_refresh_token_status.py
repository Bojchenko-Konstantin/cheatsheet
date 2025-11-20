"""populate_md_refresh_token_status

Revision ID: 6e1f23a9de9e
Revises: bd475c306381
Create Date: 2025-11-20 23:34:14.524196

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e1f23a9de9e"
down_revision: Union[str, None] = "bd475c306381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        INSERT INTO md_refresh_token_status (name) VALUES
        ('active'),
        ('revoked'),
        ('expired')
    """
    )


def downgrade():
    op.execute(
        """DELETE FROM md_refresh_token_status
        WHERE name IN ('active', 'revoked', 'expired')"""
    )
