"""create uuid v7 function

Revision ID: 77b6e2e41c37
Revises: 3434ab130e52
Create Date: 2025-09-27 15:52:18.268617

"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "77b6e2e41c37"
down_revision: Union[str, None] = "3434ab130e52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    uuid_v7_functions = Path(__file__).parent.parent / "functions" / "uuid_v7"
    op.execute((uuid_v7_functions / "upgrade.sql").read_text())


def downgrade() -> None:
    """Downgrade schema."""
    uuid_v7_functions = Path(__file__).parent.parent / "functions" / "uuid_v7"
    op.execute((uuid_v7_functions / "downgrade.sql").read_text())
