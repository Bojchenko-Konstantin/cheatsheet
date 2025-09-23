import contextlib
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import docker
import pytest
import pytest_asyncio
from docker import errors
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.infrastructure.database.database import DEFAULT_SESSION_FACTORY


class HealthcheckStatus(str, Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class UnhealthyContainerException(Exception):
    pass


ENV_VARIABLES: dict[str, Any] = {
    "dbname": settings.database.db_name,
    "username": settings.database.db_user,
    "port": settings.database.db_port,
    "password": settings.database.db_password,
}


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


DATABASE_ENV = DatabaseConfig(
    host="localhost",
    port=settings.database.db_port,
    dbname=settings.database.db_name,
    user=settings.database.db_user,
    password=settings.database.db_password,
)


@pytest.fixture(scope="session", autouse=True)
def setup_containers(request):
    client = docker.from_env()

    with contextlib.suppress(errors.APIError):
        client.networks.create(name="test", driver="bridge")

    postgres_test = client.containers.run(
        image="postgres:17-alpine",
        environment={
            "POSTGRES_DB": DATABASE_ENV.dbname,
            "POSTGRES_PASSWORD": DATABASE_ENV.password,
            "POSTGRES_USER": DATABASE_ENV.user,
        },
        healthcheck={
            "test": [
                "CMD-SHELL",
                f"pg_isready -U {DATABASE_ENV.user} -d {DATABASE_ENV.dbname}",
            ],
            "interval": 5 * 10**9,
            "retries": 5,
            "timeout": 5 * 10**9,
            "start_period": 10**10,
        },
        network="test",
        hostname="postgres-host",
        name="postgres-test",
        ports={"5432/tcp": DATABASE_ENV.port},
        detach=True,
    )

    postgres_test.reload()

    while (
        status := postgres_test.attrs["State"]["Health"]["Status"]
    ) != HealthcheckStatus.HEALTHY:
        if status == HealthcheckStatus.UNHEALTHY:
            raise UnhealthyContainerException("Container healthcheck failed")
        postgres_test.reload()
        time.sleep(1)

    try:
        migrations_image = client.images.get("migrations:latest")
    except errors.ImageNotFound:
        migrations_image, _ = client.images.build(
            path=".",
            dockerfile="tests.Dockerfile",
            tag="migrations:latest",
            forcerm=True,
            nocache=True,
        )
    migrations = client.containers.run(
        image=migrations_image,
        environment={
            "DATABASE__DB_NAME": DATABASE_ENV.dbname,
            "DATABASE__DB_PASSWORD": DATABASE_ENV.password,
            "DATABASE__DB_USER": DATABASE_ENV.user,
            "DATABASE__DB_HOST": "postgres-host",
            "DATABASE__DB_PORT": "5432",
        },
        network="test",
        detach=True,
        remove=True,
        auto_remove=True,
    )
    migrations.wait()

    def remove_containers():
        postgres_test.stop()
        postgres_test.remove()

    request.addfinalizer(remove_containers)


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
