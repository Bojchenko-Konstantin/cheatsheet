from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import RefreshToken
from src.application.interfaces.repositories.jwt import IJWTRepo
from src.infrastructure.database.models.refresh_token import RefreshTokenModel


class SQLAlchemyJWTRepo(IJWTRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, refresh_token: RefreshToken) -> None:
        model = RefreshTokenModel(
            user_id=refresh_token.user_id,
            hashed_token=refresh_token.token_hash,
            hashed_fingerprint=refresh_token.fingerprint_hash,
            expires_at=refresh_token.expires_at,
        )
        self._session.add(model)
