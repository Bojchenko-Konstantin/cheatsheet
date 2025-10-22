import subprocess
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

import docker
import pytest
import pytest_asyncio
from docker import DockerClient
from docker.models.containers import Container
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.entities import Tag
from src.infrastructure.database import DEFAULT_SESSION_FACTORY

START_INDEX: int = 1


class HealthcheckStatus(StrEnum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class UnhealthyContainerError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    internal_container_port: str


DATABASE_ENV = DatabaseConfig(
    host=settings.database.db_host,
    port=settings.database.db_port,
    dbname=settings.database.db_name,
    user=settings.database.db_user,
    password=settings.database.db_password,
    internal_container_port="5432",
)


@pytest.fixture(scope="session", autouse=True)
def test_environment_lifecycle(request) -> None:
    client = _create_docker_client()

    postgres_container = _setup_postgres_container(client)

    _wait_for_container_healthcheck(postgres_container)

    _run_database_migrations()

    def remove_container():
        postgres_container.stop()
        postgres_container.remove()

    request.addfinalizer(remove_container)


def _create_docker_client() -> DockerClient:
    return docker.from_env()


def _setup_postgres_container(client: DockerClient) -> Container:
    container = client.containers.run(
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
        ports={f"{DATABASE_ENV.internal_container_port}/tcp": DATABASE_ENV.port},
        detach=True,
    )
    return container


def _wait_for_container_healthcheck(container: Container) -> None:
    container.reload()
    while (
        status := container.attrs["State"]["Health"]["Status"]
    ) != HealthcheckStatus.HEALTHY:
        if status == HealthcheckStatus.UNHEALTHY:
            raise UnhealthyContainerError("Container healthcheck failed")
        time.sleep(1)
        container.reload()


def _run_database_migrations() -> None:
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)


@pytest_asyncio.fixture()
async def populate_db_for_single_cheatsheet() -> AsyncGenerator[tuple[UUID, set[Tag]]]:
    session = DEFAULT_SESSION_FACTORY()
    cheatsheet_quantity = 1 + START_INDEX
    tag_quantity = 3 + START_INDEX

    cheatsheet_id = await _populate_cheatsheet(session, quantity=cheatsheet_quantity)
    await _populate_md_tag(session, quantity=tag_quantity)
    await _populate_cheatsheet_stats(
        session, quantity=cheatsheet_quantity, cheatsheet_id=cheatsheet_id
    )
    await _populate_cheatsheet_to_tag(session)
    tags = await _get_required_tags(session, cheatsheet_id)

    yield cheatsheet_id, tags

    await _truncate_all_tables(session)


async def _populate_cheatsheet(session: AsyncSession, quantity: int) -> UUID:
    query = text(
        """INSERT INTO cheatsheet(title, content, is_public, created_at, updated_at)
           VALUES (:title, :content, :is_public, :created_at, :updated_at)
           RETURNING cheatsheet_id"""
    )

    test_date = datetime(2025, 1, 1)
    data = [
        {
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
            ORDER BY tag_id)"""
    )

    await session.execute(query)
    await session.commit()


async def _get_required_tags(session: AsyncSession, cheatsheet_id: UUID) -> set[Tag]:
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
    tags = {Tag(tag_id, tag_name) for tag_id, tag_name in raw_tags}

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
