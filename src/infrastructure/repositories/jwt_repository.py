from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.repositories.utils import DictBundle
from src.application.dto import RefreshToken, TokenStatus
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

    async def get_device_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshToken]:
        statement = (
            select(
                DictBundle(
                    "refresh_token",
                    RefreshTokenModel.hashed_token,
                    RefreshTokenModel.expires_at,
                    RefreshTokenModel.status_id,
                )
            )
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.hashed_fingerprint == fingerprint,
                RefreshTokenModel.status_id != TokenStatus.COMPROMISED,
            )
            .order_by(
                RefreshTokenModel.status_id,
                RefreshTokenModel.expires_at,
            )
        )
        result = await self._session.execute(statement)
        [raw_tokens] = result.all()

        if not raw_tokens:
            raise

        tokens = [
            RefreshToken.from_dict(dict(user_id=user_id, **token_data))
            for token_data in raw_tokens.refresh_token
        ]

        return tokens

    async def _revoke_older_refresh_token(self, user_id: UUID) -> None:
        update_statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.status_id == TokenStatus.ACTIVE,
            )
            .values(
                status_id=TokenStatus.REVOKED, revoked_at=datetime.now(tz=timezone.utc)
            )
        )

        try:
            await self._session.execute(update_statement)

        except Exception:
            raise
