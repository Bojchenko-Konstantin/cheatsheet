"""replace cheatsheet_id on the first place

Revision ID: 43a6f66a8aa3
Revises: 85aa65b32d12
Create Date: 2025-09-27 19:32:13.372660

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "43a6f66a8aa3"
down_revision: Union[str, None] = "85aa65b32d12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cheatsheet_to_tag_tag_id_md_tag", "cheatsheet_to_tag", type_="foreignkey"
    )

    op.create_table(
        "cheatsheet_stats_temp",
        sa.Column("cheatsheet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "count_like", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "count_view", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
    )

    op.execute(
        """
        INSERT INTO cheatsheet_stats_temp (cheatsheet_id, count_like, count_view)
        SELECT cheatsheet_id, count_like, count_view FROM cheatsheet_stats
    """
    )

    op.drop_table("cheatsheet_stats")
    op.rename_table("cheatsheet_stats_temp", "cheatsheet_stats")

    op.create_table(
        "cheatsheet_to_tag_temp",
        sa.Column("cheatsheet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", sa.BigInteger(), nullable=False),
    )

    op.execute(
        """
        INSERT INTO cheatsheet_to_tag_temp (cheatsheet_id, tag_id)
        SELECT cheatsheet_id, tag_id FROM cheatsheet_to_tag
    """
    )

    op.drop_table("cheatsheet_to_tag")
    op.rename_table("cheatsheet_to_tag_temp", "cheatsheet_to_tag")

    op.create_table(
        "cheatsheet_temp",
        sa.Column(
            "cheatsheet_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v7()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "is_public", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
    )

    op.execute(
        """
        INSERT INTO cheatsheet_temp (cheatsheet_id, title, content, created_at,
        updated_at, is_public)
        SELECT cheatsheet_id, title, content, created_at, updated_at, is_public
        FROM cheatsheet
    """
    )

    op.drop_table("cheatsheet")
    op.rename_table("cheatsheet_temp", "cheatsheet")

    op.create_primary_key("pk_cheatsheet", "cheatsheet", ["cheatsheet_id"])
    op.create_unique_constraint("uq_cheatsheet_title", "cheatsheet", ["title"])

    op.create_primary_key("pk_cheatsheet_stats", "cheatsheet_stats", ["cheatsheet_id"])
    op.create_foreign_key(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_count_like_positive", "cheatsheet_stats", "count_like >= 0"
    )
    op.create_check_constraint(
        "ck_count_view_positive", "cheatsheet_stats", "count_view >= 0"
    )

    op.create_primary_key(
        "pk_cheatsheet_to_tag", "cheatsheet_to_tag", ["cheatsheet_id", "tag_id"]
    )
    op.create_foreign_key(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
    )
    op.create_foreign_key(
        "fk_cheatsheet_to_tag_tag_id_md_tag",
        "cheatsheet_to_tag",
        "md_tag",
        ["tag_id"],
        ["tag_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_cheatsheet_to_tag_tag_id_md_tag", "cheatsheet_to_tag", type_="foreignkey"
    )

    op.create_table(
        "cheatsheet_old",
        sa.Column("title", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "is_public", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "cheatsheet_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v7()"),
            nullable=False,
        ),
    )

    op.execute(
        """
        INSERT INTO cheatsheet_old (title, content, created_at, updated_at, is_public,
        cheatsheet_id)
        SELECT title, content, created_at, updated_at, is_public, cheatsheet_id
        FROM cheatsheet
    """
    )

    op.drop_table("cheatsheet")
    op.rename_table("cheatsheet_old", "cheatsheet")

    op.create_table(
        "cheatsheet_to_tag_old",
        sa.Column("tag_id", sa.BigInteger(), nullable=False),
        sa.Column("cheatsheet_id", postgresql.UUID(as_uuid=True), nullable=False),
    )

    op.execute(
        """
        INSERT INTO cheatsheet_to_tag_old (tag_id, cheatsheet_id)
        SELECT tag_id, cheatsheet_id FROM cheatsheet_to_tag
    """
    )

    op.drop_table("cheatsheet_to_tag")
    op.rename_table("cheatsheet_to_tag_old", "cheatsheet_to_tag")

    op.create_table(
        "cheatsheet_stats_old",
        sa.Column(
            "count_like", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "count_view", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("cheatsheet_id", postgresql.UUID(as_uuid=True), nullable=False),
    )

    op.execute(
        """
        INSERT INTO cheatsheet_stats_old (count_like, count_view, cheatsheet_id)
        SELECT count_like, count_view, cheatsheet_id FROM cheatsheet_stats
    """
    )

    op.drop_table("cheatsheet_stats")
    op.rename_table("cheatsheet_stats_old", "cheatsheet_stats")

    op.create_primary_key("pk_cheatsheet", "cheatsheet", ["cheatsheet_id"])
    op.create_unique_constraint("uq_cheatsheet_title", "cheatsheet", ["title"])

    op.create_primary_key("pk_cheatsheet_stats", "cheatsheet_stats", ["cheatsheet_id"])
    op.create_foreign_key(
        "fk_cheatsheet_stats_cheatsheet_id_cheatsheet",
        "cheatsheet_stats",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_count_like_positive", "cheatsheet_stats", "count_like >= 0"
    )
    op.create_check_constraint(
        "ck_count_view_positive", "cheatsheet_stats", "count_view >= 0"
    )

    op.create_primary_key(
        "pk_cheatsheet_to_tag", "cheatsheet_to_tag", ["cheatsheet_id", "tag_id"]
    )
    op.create_foreign_key(
        "fk_cheatsheet_to_tag_cheatsheet_id_cheatsheet",
        "cheatsheet_to_tag",
        "cheatsheet",
        ["cheatsheet_id"],
        ["cheatsheet_id"],
    )
    op.create_foreign_key(
        "fk_cheatsheet_to_tag_tag_id_md_tag",
        "cheatsheet_to_tag",
        "md_tag",
        ["tag_id"],
        ["tag_id"],
    )
