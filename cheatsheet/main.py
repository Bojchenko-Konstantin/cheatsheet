from contextlib import asynccontextmanager

import uvicorn
from core.database.database_helper import db_helper
from core.logging_config import setup_logging
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

setup_logging()


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
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
    )
