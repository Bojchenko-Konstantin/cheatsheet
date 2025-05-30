from contextlib import asynccontextmanager
from logging.config import dictConfig

import uvicorn
from database.database_helper import db_helper
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from logging_config import LOGGING

dictConfig(LOGGING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI is initialized, but does not accept requests yet.
    # Here you can, for example, check the connection to the database.
    yield
    # Ensures that all database connections are closed gracefully
    # when the application terminates
    await db_helper.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)  # type: ignore[unused-ignore]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
    )
