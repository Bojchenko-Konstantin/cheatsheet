from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.cheatsheet import CheatsheetUseCase
from infrastructure.database.database_helper import db_helper
from infrastructure.repositories.cheatsheet_repository import (
    SQLAlchemyCheatsheetRepository,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_helper.session_getter():
        yield session


async def get_cheatsheet_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyCheatsheetRepository:
    return SQLAlchemyCheatsheetRepository(session)


async def get_cheatsheet_use_case(
    repo: SQLAlchemyCheatsheetRepository = Depends(get_cheatsheet_repo),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(repo=repo)
