from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import UUID

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

type CheatsheetTestRecord = tuple[UUID, UUID, list[dict]]

START_INDEX: int = 1


@pytest_asyncio.fixture
async def populate_db_for_single_cheatsheet(
    session: AsyncSession,
) -> AsyncGenerator[CheatsheetTestRecord]:
    cheatsheet_quantity = 1 + START_INDEX
    tag_quantity = 3 + START_INDEX

    user_id = await _populate_user(session)
    cheatsheet_id = await _populate_cheatsheet(
        session, user_id, quantity=cheatsheet_quantity
    )
    await _populate_md_tag(session, quantity=tag_quantity)
    await _populate_cheatsheet_stats(
        session, quantity=cheatsheet_quantity, cheatsheet_id=cheatsheet_id
    )
    await _populate_cheatsheet_to_tag(session)
    tags = await _get_required_tags(session, cheatsheet_id)

    yield cheatsheet_id, user_id, tags

    await _truncate_all_tables(session)


@pytest_asyncio.fixture
async def populate_db_for_cheatsheet_list() -> AsyncGenerator[None]:
    session = DEFAULT_SESSION_FACTORY()

    await _truncate_all_tables(session)

    user_id = await _populate_user(session, suffix="_list")
    cheatsheet_ids = await _populate_cheatsheets_for_list(session, user_id)
    await _populate_tags_for_list(session)
    await _populate_cheatsheet_stats_for_list(session, cheatsheet_ids)
    await _populate_cheatsheet_to_tag_for_list(session, cheatsheet_ids)

    yield

    await _truncate_all_tables(session)
    await session.close()


async def _populate_user(session: AsyncSession, suffix: str = "") -> UUID:
    query = text(
        """INSERT INTO "user"(user_name, is_verified, is_active,
                              is_superuser, email, hashed_password)
           VALUES (:user_name, :is_verified, :is_active,
                   :is_superuser, :email, :hashed_password)
           RETURNING user_id"""
    )

    data = [
        {
            "user_name": f"test{suffix}",
            "is_verified": True,
            "is_active": True,
            "is_superuser": False,
            "email": f"test{suffix}@random.mail",
            "hashed_password": "hashed_password",
        }
    ]

    result = await session.execute(query, data)
    [user_id] = result.first()  # type: ignore

    return user_id


async def _populate_cheatsheet(
    session: AsyncSession, user_id: UUID, quantity: int
) -> UUID:
    query = text(
        """INSERT INTO cheatsheet(user_id, title, content,
                                  is_public, created_at, updated_at)
           VALUES (:user_id, :title, :content, :is_public, :created_at, :updated_at)
           RETURNING cheatsheet_id"""
    )

    test_date = datetime(2025, 1, 1)
    data = [
        {
            "user_id": user_id,
            "title": f"title_{value}",
            "content": f"content_{value}",
            "is_public": _is_even(value),
            "created_at": test_date,
            "updated_at": test_date,
        }
        for value in range(START_INDEX, quantity)
    ]

    result = await session.execute(query, data)
    [cheatsheet_id] = result.first()  # type: ignore

    return cheatsheet_id


def _is_even(value: int) -> bool:
    return value % 2 == 0


async def _populate_md_tag(session: AsyncSession, quantity: int) -> None:
    query = text("""INSERT INTO md_tag(tag_name) VALUES (:tag_name)""")
    data = [{"tag_name": f"tag_name_{value}"} for value in range(START_INDEX, quantity)]

    await session.execute(query, data)
    await session.commit()


async def _populate_tags_for_list(session: AsyncSession) -> None:
    tag_names = ["python", "fastapi", "postgresql", "django"]
    query = text("""INSERT INTO md_tag(tag_name) VALUES (:tag_name)""")

    for name in tag_names:
        await session.execute(query, {"tag_name": name})

    await session.commit()


async def _populate_cheatsheet_stats(
    session: AsyncSession, quantity: int, cheatsheet_id: UUID
) -> None:
    query = text(
        """INSERT INTO cheatsheet_stats(cheatsheet_id, count_like, count_view)
           VALUES (:cheatsheet_id, :count_like, :count_view)"""
    )

    data = [
        {"cheatsheet_id": cheatsheet_id, "count_like": value, "count_view": value}
        for value in range(START_INDEX, quantity)
    ]

    await session.execute(query, data)
    await session.commit()


async def _populate_cheatsheet_to_tag(session: AsyncSession) -> None:
    query = text(
        """INSERT INTO cheatsheet_to_tag(cheatsheet_id, tag_id) (
               SELECT cheatsheet_id, tag_id
               FROM cheatsheet
               CROSS JOIN md_tag
               ORDER BY tag_id
           )"""
    )

    await session.execute(query)
    await session.commit()


async def _get_required_tags(
    session: AsyncSession, cheatsheet_id: UUID
) -> list[dict[str, str | int]]:
    query = text(
        """SELECT tag_id, tag_name
           FROM md_tag
           JOIN cheatsheet_to_tag USING(tag_id)
           JOIN cheatsheet USING(cheatsheet_id)
           WHERE cheatsheet_id = :cheatsheet_id"""
    )

    data = {"cheatsheet_id": cheatsheet_id}

    result = await session.execute(query, data)
    await session.commit()
    raw_tags = result.all()
    tags = [{"tag_id": tag_id, "tag_name": tag_name} for tag_id, tag_name in raw_tags]

    return tags


async def _populate_cheatsheets_for_list(
    session: AsyncSession, user_id: UUID
) -> list[UUID]:
    cheatsheets = [
        {
            "user_id": user_id,
            "title": "Python Basics",
            "content": "Python fundamentals",
            "is_public": True,
            "created_at": datetime(2026, 5, 6, 12, 0, 0),
            "updated_at": datetime(2026, 5, 6, 12, 0, 0),
        },
        {
            "user_id": user_id,
            "title": "FastAPI Tutorial",
            "content": "Building APIs",
            "is_public": True,
            "created_at": datetime(2026, 5, 6, 12, 0, 1),
            "updated_at": datetime(2026, 5, 6, 12, 0, 1),
        },
        {
            "user_id": user_id,
            "title": "PostgreSQL Guide",
            "content": "Database tips",
            "is_public": True,
            "created_at": datetime(2026, 5, 6, 12, 0, 2),
            "updated_at": datetime(2026, 5, 6, 12, 0, 2),
        },
        {
            "user_id": user_id,
            "title": "Private Cheatsheet",
            "content": "Secret content",
            "is_public": False,
            "created_at": datetime(2026, 5, 6, 12, 0, 3),
            "updated_at": datetime(2026, 5, 6, 12, 0, 3),
        },
        {
            "user_id": user_id,
            "title": "Django Web Framework",
            "content": "Django basics",
            "is_public": True,
            "created_at": datetime(2026, 5, 6, 12, 0, 4),
            "updated_at": datetime(2026, 5, 6, 12, 0, 4),
        },
    ]

    query = text(
        """INSERT INTO cheatsheet(user_id, title, content,
                                  is_public, created_at, updated_at)
           VALUES (:user_id, :title, :content, :is_public, :created_at, :updated_at)
           RETURNING cheatsheet_id"""
    )

    ids = []
    for data in cheatsheets:
        result = await session.execute(query, data)
        [cheatsheet_id] = result.first()  # type: ignore
        ids.append(cheatsheet_id)

    await session.commit()
    return ids


async def _populate_cheatsheet_stats_for_list(
    session: AsyncSession, cheatsheet_ids: list[UUID]
) -> None:
    query = text(
        """INSERT INTO cheatsheet_stats(cheatsheet_id, count_like, count_view)
           VALUES (:cheatsheet_id, 0, 0)"""
    )

    for cheatsheet_id in cheatsheet_ids:
        await session.execute(query, {"cheatsheet_id": cheatsheet_id})

    await session.commit()


async def _populate_cheatsheet_to_tag_for_list(
    session: AsyncSession, cheatsheet_ids: list[UUID]
) -> None:
    tag_assignments = [
        (cheatsheet_ids[0], 1),  # Python Basics -> tag 1
        (cheatsheet_ids[1], 2),  # FastAPI Tutorial -> tag 2
        (cheatsheet_ids[2], 3),  # PostgreSQL Guide -> tag 3
        (cheatsheet_ids[4], 4),  # Django -> tag 4
    ]

    query = text(
        """INSERT INTO cheatsheet_to_tag(cheatsheet_id, tag_id)
           VALUES (:cheatsheet_id, :tag_id)
           ON CONFLICT DO NOTHING"""
    )

    for cheatsheet_id, tag_id in tag_assignments:
        await session.execute(
            query,
            {
                "cheatsheet_id": cheatsheet_id,
                "tag_id": tag_id,
            },
        )

    await session.commit()


async def _truncate_all_tables(session: AsyncSession) -> None:
    query = text(
        """TRUNCATE cheatsheet,
                    "user",
                    md_tag,
                    cheatsheet_stats,
                    cheatsheet_to_tag
           RESTART IDENTITY
           CASCADE"""
    )

    await session.execute(query)
    await session.commit()
