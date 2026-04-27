import subprocess
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from smtplib import SMTP
from typing import Any

import docker
import pytest
from docker import DockerClient
from docker.models.containers import Container
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from httpx import ASGITransport, AsyncClient
from taskiq import (
    InMemoryBroker,
    async_shared_broker,
)

from src.core.config import settings
from src.main import router_auth, router_cheatsheet


class HealthcheckStatus(StrEnum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class UnhealthyContainerError(Exception):
    pass


class FakeNotificationUseCase:
    async def send_welcome_email(self, data: Any) -> None:
        with SMTP(host="localhost", port=1025) as client:
            client.sendmail(
                from_addr="sender@test.com",
                to_addrs="user@example.com",
                msg="Hello, test",
            )


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


@pytest.fixture(autouse=True)
async def broker():
    test_broker = InMemoryBroker(await_inplace=True)
    async_shared_broker.default_broker(test_broker)
    test_broker.state.notification_use_case = FakeNotificationUseCase()

    await test_broker.startup()
    yield test_broker
    await test_broker.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    yield


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI(
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    app.include_router(router_cheatsheet)
    app.include_router(router_auth)
    return app


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def test_environment_lifecycle(request) -> None:
    client = _create_docker_client()

    postgres_container = _setup_postgres_container(client)
    smtp_container = _setup_smtp_container(client)

    _wait_for_container_healthcheck(postgres_container)
    _wait_for_container_healthcheck(smtp_container)

    _run_database_migrations()

    def remove_containers():
        postgres_container.stop()
        postgres_container.remove()

        smtp_container.stop()
        smtp_container.remove()

    request.addfinalizer(remove_containers)


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
        command=[
            "postgres",
            "-c",
            "fsync=off",
            "-c",
            "full_page_writes=off",
            "-c",
            "log_statement=none",
            "-c",
            "log_min_messages=warning",
            "-c",
            "synchronous_commit=off",
        ],
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
        tmpfs={"/var/lib/postgresql/data": "size=512m"},
        detach=True,
    )
    return container


def _setup_smtp_container(client: DockerClient) -> Container:
    container = client.containers.run(
        image="mailhog/mailhog",
        healthcheck={
            "test": [
                "CMD-SHELL",
                "wget --no-verbose --tries=1 --spider http://localhost:8025/api/v2/messages",
            ],
            "interval": 5 * 10**9,
            "retries": 5,
            "timeout": 5 * 10**9,
            "start_period": 5**10,
        },
        ports={
            "1025": 1025,
            "8025": 8025,
        },
        detach=True,
        hostname="mailhog",
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
