from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.v1.routers.cheatsheet import router as router_cheatsheet
from src.core.logging_config import setup_logging
from src.infrastructure.database import dispose


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    setup_logging()
    yield
    await dispose()


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
