from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import RefreshToken
from src.application.interfaces.repositories.jwt import IJWTRepo
from src.infrastructure.database.models.refresh_token import RefreshTokenModel


class SQLAlchemyJWTRepo(IJWTRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, refresh_token: RefreshToken) -> None:
        await self._revoke_older_refresh_token(refresh_token.user_id)  # type: ignore

        model = RefreshTokenModel(
            user_id=refresh_token.user_id,
            hashed_token=refresh_token.token_hash,
            hashed_fingerprint=refresh_token.fingerprint_hash,
            expires_at=refresh_token.expires_at,
        )
        self._session.add(model)

    async def _revoke_older_refresh_token(self, user_id: UUID):
        update_statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id, RefreshTokenModel.status_id == 1
            )
            .values(status_id=2, revoked_at=datetime.now(tz=timezone.utc))
        )

        try:
            await self._session.execute(update_statement)

        except Exception:
            raise
