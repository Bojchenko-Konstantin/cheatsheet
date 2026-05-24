"""enable_pg_trgm_extension

Revision ID: 1f2a7fe2d4b6
Revises: 8577528d0c23
Create Date: 2026-05-06 23:30:49.182035

"""

from alembic import op

revision = "1f2a7fe2d4b6"
down_revision = "8577528d0c23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
