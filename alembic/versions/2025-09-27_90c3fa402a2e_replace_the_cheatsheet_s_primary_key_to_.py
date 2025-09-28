"""replace the cheatsheet's primary key to UUID instead of int

Revision ID: 90c3fa402a2e
Revises: 77b6e2e41c37
Create Date: 2025-09-27 16:38:36.956453

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "90c3fa402a2e"
down_revision: Union[str, None] = "77b6e2e41c37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cheatsheet",
        sa.Column(
            "new_uuid",
            sa.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v7()"),
            nullable=False,
        ),
    )

    op.add_column(
        "cheatsheet_to_tag",
        sa.Column("cheatsheet_uuid_temp", sa.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "cheatsheet_stats",
        sa.Column("cheatsheet_uuid_temp", sa.UUID(as_uuid=True), nullable=True),
    )

    update_cheatsheet_to_tag_query = """
        UPDATE cheatsheet_to_tag
        SET cheatsheet_uuid_temp = cheatsheet.new_uuid
        FROM cheatsheet
        WHERE cheatsheet_to_tag.cheatsheet_id = cheatsheet.cheatsheet_id
    """
    op.execute(update_cheatsheet_to_tag_query)

    update_cheatsheet_stats_query = """
        UPDATE cheatsheet_stats
        SET cheatsheet_uuid_temp = cheatsheet.new_uuid
        FROM cheatsheet
        WHERE cheatsheet_stats.cheatsheet_id = cheatsheet.cheatsheet_id
    """
    op.execute(update_cheatsheet_stats_query)

    op.drop_constraint(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        type_="foreignkey",
    )

    op.drop_column("cheatsheet_to_tag", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_to_tag", "cheatsheet_uuid_temp", new_column_name="cheatsheet_id"
    )

    op.drop_column("cheatsheet_stats", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_stats", "cheatsheet_uuid_temp", new_column_name="cheatsheet_id"
    )

    op.drop_constraint("pk_cheatsheet", "cheatsheet", type_="primary")
    op.drop_constraint("uq_cheatsheet_title", "cheatsheet", type_="unique")

    op.drop_column("cheatsheet", "cheatsheet_id")
    op.alter_column("cheatsheet", "new_uuid", new_column_name="cheatsheet_id")

    op.create_primary_key("pk_cheatsheet", "cheatsheet", ["cheatsheet_id"])
    op.create_unique_constraint("uq_cheatsheet_title", "cheatsheet", ["title"])

    op.create_foreign_key(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
    )

    op.create_foreign_key(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "cheatsheet",
        sa.Column(
            "old_id_temp", sa.BIGINT(), sa.Identity(start=1, increment=1), nullable=True
        ),
    )

    op.execute(
        """
        UPDATE cheatsheet
        SET old_id_temp = nextval(pg_get_serial_sequence('cheatsheet', 'cheatsheet_id'))
    """
    )

    op.add_column(
        "cheatsheet_to_tag", sa.Column("cheatsheet_id_temp", sa.BIGINT(), nullable=True)
    )
    op.add_column(
        "cheatsheet_stats", sa.Column("cheatsheet_id_temp", sa.BIGINT(), nullable=True)
    )

    update_cheatsheet_to_tag_query = """
        UPDATE cheatsheet_to_tag
        SET cheatsheet_id_temp = cheatsheet.old_id_temp
        FROM cheatsheet
        WHERE cheatsheet_to_tag.cheatsheet_id = cheatsheet.cheatsheet_id
    """
    op.execute(update_cheatsheet_to_tag_query)

    update_cheatsheet_stats_query = """
        UPDATE cheatsheet_stats
        SET cheatsheet_id_temp = cheatsheet.old_id_temp
        FROM cheatsheet
        WHERE cheatsheet_stats.cheatsheet_id = cheatsheet.cheatsheet_id
    """
    op.execute(update_cheatsheet_stats_query)

    op.drop_constraint(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        type_="foreignkey",
    )

    op.drop_column("cheatsheet_to_tag", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_to_tag", "cheatsheet_id_temp", new_column_name="cheatsheet_id"
    )

    op.drop_column("cheatsheet_stats", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_stats", "cheatsheet_id_temp", new_column_name="cheatsheet_id"
    )

    op.drop_constraint("pk_cheatsheet", "cheatsheet", type_="primary")
    op.drop_constraint("uq_cheatsheet_title", "cheatsheet", type_="unique")

    op.drop_column("cheatsheet", "cheatsheet_id")
    op.alter_column("cheatsheet", "old_id_temp", new_column_name="cheatsheet_id")

    op.create_primary_key("pk_cheatsheet", "cheatsheet", ["cheatsheet_id"])
    op.create_unique_constraint("uq_cheatsheet_title", "cheatsheet", ["title"])

    op.create_foreign_key(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
    )

    op.create_foreign_key(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
        ondelete="CASCADE",
    )

    op.execute(
        """
        SELECT setval(pg_get_serial_sequence('cheatsheet', 'cheatsheet_id'),
                     COALESCE((SELECT MAX(cheatsheet_id) FROM cheatsheet), 1))
    """
    )
