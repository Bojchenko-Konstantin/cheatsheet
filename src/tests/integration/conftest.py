import os
import subprocess
import time
from collections.abc import Iterator
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.database import DEFAULT_SESSION_FACTORY


@pytest.fixture(scope="session", autouse=True)
def manage_db_container() -> Iterator[None]:
    _run_db_container()
    time.sleep(5)
    yield
    _down_db_container()


def _run_db_container() -> None:
    env_file = os.getenv("ENV_FILE", ".env.test")
    command = [
        "docker",
        "compose",
        "--env-file",
        env_file,
        "-f",
        "compose.test.yaml",
        "up",
        "-d",
        "--build",
    ]
    subprocess.run(
        command,
        capture_output=True,
        check=True,
        text=True,
    )


def _down_db_container() -> None:
    env_file = os.getenv("ENV_FILE", ".env.test")
    command = [
        "docker",
        "compose",
        "--env-file",
        env_file,
        "-f",
        "compose.test.yaml",
        "down",
    ]
    subprocess.run(
        command,
        capture_output=True,
        check=True,
        text=True,
    )


@pytest_asyncio.fixture()
async def populate_db_for_single_cheatsheet():
    session = DEFAULT_SESSION_FACTORY()
    cheatsheet_id = await _populate_cheatsheet(session, quantity=2)
    await _populate_md_tag(session, quantity=10)
    await _populate_cheatsheet_stats(session, quantity=2)
    await _populate_cheatsheet_to_tag(session, quantity=3)
    tags = await _get_required_tags(session, cheatsheet_id)

    yield cheatsheet_id, tags

    await _truncate_all_tables(session)


async def _populate_cheatsheet(session: AsyncSession, quantity: int) -> int:
    query = text(
        """INSERT INTO cheatsheet(title, content, is_public, created_at, updated_at)
           VALUES (:title, :content, :is_public, :created_at, :updated_at)
           RETURNING cheatsheet_id"""
    )
    data = [
        {
            "title": f"title_{value}",
            "content": f"content_{value}",
            "is_public": value % 2 == 0,
            "created_at": datetime(2025, 1, 1),
            "updated_at": datetime(2025, 1, 1),
        }
        for value in range(1, quantity)
    ]
    result = await session.execute(query, data)
    [cheatsheet_id] = result.first()  # type: ignore
    return cheatsheet_id


async def _populate_md_tag(session: AsyncSession, quantity: int):
    query = text("""INSERT INTO md_tag(tag_name) VALUES (:tag_name)""")
    data = [{"tag_name": f"tag_name_{value}"} for value in range(1, quantity)]
    await session.execute(query, data)
    await session.commit()


async def _populate_cheatsheet_stats(session: AsyncSession, quantity: int):
    query = text(
        """INSERT INTO cheatsheet_stats(cheatsheet_id, count_like, count_view)
        VALUES (:cheatsheet_id, :count_like, :count_view)"""
    )
    data = [
        {"cheatsheet_id": value, "count_like": value, "count_view": value}
        for value in range(1, quantity)
    ]
    await session.execute(query, data)
    await session.commit()


async def _populate_cheatsheet_to_tag(session: AsyncSession, quantity: int):
    query = text(
        """INSERT INTO cheatsheet_to_tag(cheatsheet_id, tag_id) (
            SELECT cheatsheet_id, tag_id
            FROM cheatsheet
            CROSS JOIN md_tag
            ORDER BY tag_id
            LIMIT :limit)"""
    )
    data = [{"limit": quantity}]
    await session.execute(query, data)
    await session.commit()


async def _get_required_tags(session: AsyncSession, cheatsheet_id: int):
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
    tags = result.all()
    return tags


async def _truncate_all_tables(session: AsyncSession) -> None:
    query = text(
        """TRUNCATE cheatsheet,
                    md_tag,
                    cheatsheet_stats,
                    cheatsheet_to_tag
           RESTART IDENTITY
           CASCADE
            """
    )
    await session.execute(query)
    await session.commit()
