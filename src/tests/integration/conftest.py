import subprocess
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum

import docker
import pytest
from docker import DockerClient
from docker.models.containers import Container
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from httpx import ASGITransport, AsyncClient

from src.core.config import settings
from src.main import router_auth, router_cheatsheet


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


@asynccontextmanager
async def empty_lifespan(app: FastAPI) -> AsyncGenerator:
    yield


@pytest.fixture()
def app() -> FastAPI:
    app = FastAPI(
        default_response_class=ORJSONResponse,
        lifespan=empty_lifespan,
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
