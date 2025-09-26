FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

COPY pyproject.toml .

RUN uv sync

COPY src src/
COPY alembic alembic/
COPY alembic.ini .

CMD ["uv", "run", "alembic", "upgrade", "head"]
