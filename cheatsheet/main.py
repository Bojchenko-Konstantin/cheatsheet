from contextlib import asynccontextmanager

import uvicorn
from core.database.database_helper import db_helper
from core.logging_config import setup_logging
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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
