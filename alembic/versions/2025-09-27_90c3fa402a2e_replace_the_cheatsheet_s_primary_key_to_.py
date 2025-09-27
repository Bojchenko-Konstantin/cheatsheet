"""replace the cheatsheet's primary key to UUID instead of int

Revision ID: 90c3fa402a2e
Revises: 77b6e2e41c37
Create Date: 2025-09-27 16:38:36.956453

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "90c3fa402a2e"
down_revision: Union[str, None] = "77b6e2e41c37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Добавляем новую колонку UUID в основную таблицу
    op.add_column(
        "cheatsheet",
        sa.Column(
            "new_uuid",
            sa.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v7()"),
            nullable=False,
        ),
    )

    # 2. Добавляем временные колонки UUID во все таблицы с внешними ключами
    op.add_column(
        "cheatsheet_to_tag",
        sa.Column("cheatsheet_uuid_temp", sa.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "cheatsheet_stats",
        sa.Column("cheatsheet_uuid_temp", sa.UUID(as_uuid=True), nullable=True),
    )

    # 3. Заполняем новую колонку UUID значениями из основной таблицы
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

    # 4. Удаляем старые внешние ключи
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

    # 5. Удаляем старые колонки и переименовываем временные во всех таблицах
    # Для cheatsheet_to_tag
    op.drop_column("cheatsheet_to_tag", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_to_tag", "cheatsheet_uuid_temp", new_column_name="cheatsheet_id"
    )

    # Для cheatsheet_stats
    op.drop_column("cheatsheet_stats", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_stats", "cheatsheet_uuid_temp", new_column_name="cheatsheet_id"
    )

    # 6. Удаляем старый первичный ключ и уникальный индекс в основной таблице
    op.drop_constraint("pk_cheatsheet", "cheatsheet", type_="primary")
    op.drop_constraint("uq_cheatsheet_title", "cheatsheet", type_="unique")

    # 7. Удаляем старую колонку и переименовываем новую в основной таблице
    op.drop_column("cheatsheet", "cheatsheet_id")
    op.alter_column("cheatsheet", "new_uuid", new_column_name="cheatsheet_id")

    # 8. Восстанавливаем первичный ключ и уникальный индекс
    op.create_primary_key("pk_cheatsheet", "cheatsheet", ["cheatsheet_id"])
    op.create_unique_constraint("uq_cheatsheet_title", "cheatsheet", ["title"])

    # 9. Восстанавливаем внешние ключи
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
    # 1. Добавляем временную BIGINT колонку в основную таблицу
    op.add_column(
        "cheatsheet",
        sa.Column(
            "old_id_temp", sa.BIGINT(), sa.Identity(start=1, increment=1), nullable=True
        ),
    )

    # 2. Заполняем временную колонку последовательными значениями
    op.execute(
        """
        UPDATE cheatsheet
        SET old_id_temp = nextval(pg_get_serial_sequence('cheatsheet', 'cheatsheet_id'))
    """
    )

    # 3. Добавляем временные BIGINT колонки во все таблицы с внешними ключами
    op.add_column(
        "cheatsheet_to_tag", sa.Column("cheatsheet_id_temp", sa.BIGINT(), nullable=True)
    )
    op.add_column(
        "cheatsheet_stats", sa.Column("cheatsheet_id_temp", sa.BIGINT(), nullable=True)
    )

    # 4. Заполняем временные колонки значениями из основной таблицы
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

    # 5. Удаляем внешние ключи
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

    # 6. Удаляем UUID колонки и переименовываем временные BIGINT
    # Для cheatsheet_to_tag
    op.drop_column("cheatsheet_to_tag", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_to_tag", "cheatsheet_id_temp", new_column_name="cheatsheet_id"
    )

    # Для cheatsheet_stats
    op.drop_column("cheatsheet_stats", "cheatsheet_id")
    op.alter_column(
        "cheatsheet_stats", "cheatsheet_id_temp", new_column_name="cheatsheet_id"
    )

    # 7. Удаляем первичный ключ и уникальный индекс
    op.drop_constraint("pk_cheatsheet", "cheatsheet", type_="primary")
    op.drop_constraint("uq_cheatsheet_title", "cheatsheet", type_="unique")

    # 8. Удаляем UUID колонку и переименовываем временную BIGINT
    op.drop_column("cheatsheet", "cheatsheet_id")
    op.alter_column("cheatsheet", "old_id_temp", new_column_name="cheatsheet_id")

    # 9. Восстанавливаем первичный ключ и уникальный индекс
    op.create_primary_key("pk_cheatsheet", "cheatsheet", ["cheatsheet_id"])
    op.create_unique_constraint("uq_cheatsheet_title", "cheatsheet", ["title"])

    # 10. Восстанавливаем внешние ключи
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

    # 11. Восстанавливаем identity sequence
    op.execute(
        """
        SELECT setval(pg_get_serial_sequence('cheatsheet', 'cheatsheet_id'),
                     COALESCE((SELECT MAX(cheatsheet_id) FROM cheatsheet), 1))
    """
    )
