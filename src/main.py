from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1.routers.cheatsheet import router as router_cheatsheet
from core.logging_config import setup_logging
from infrastructure.database.database_helper import db_helper

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db_helper.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(router_cheatsheet)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
    )
