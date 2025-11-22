from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.jwt import IJWTRepo


class SQLAlchemyJWTRepo(IJWTRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, token_hash: str, expires_at: datetime) -> None:
        pass
