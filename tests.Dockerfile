FROM ghcr.io/astral-sh/uv:python3.13-alpine as base

WORKDIR /app

COPY pyproject.toml .

RUN uv sync

COPY src src/

FROM base AS migrations

COPY alembic alembic/
COPY alembic.ini .

CMD ["uv", "run", "alembic", "upgrade", "head"]

FROM base AS tests

CMD ["uv", "run", "pytest", "-m", "integration"]
