import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import RefreshToken, TokenStatus
from src.application.interfaces.repositories.jwt import IJWTRepo
from src.infrastructure.database.models.refresh_token import RefreshTokenModel
from src.infrastructure.database.models.refresh_token_blacklist import (
    RefreshTokenBlacklistModel,
)
from src.infrastructure.repositories.utils import DictBundle

logger = logging.getLogger(__name__)


class SQLAlchemyJWTRepo(IJWTRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, refresh_token: RefreshToken) -> None:
        await self._move_older_refresh_token_to_blacklist(
            refresh_token.user_id,  # type: ignore
            refresh_token.hashed_fingerprint,  # type: ignore
        )

        model = RefreshTokenModel(
            user_id=refresh_token.user_id,
            hashed_token=refresh_token.hashed_token,
            hashed_fingerprint=refresh_token.hashed_fingerprint,
            expires_at=refresh_token.expires_at,
        )
        self._session.add(model)

    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshToken:
        statement = select(
            DictBundle(
                "refresh_token",
                RefreshTokenModel.hashed_token,
                RefreshTokenModel.expires_at,
                RefreshTokenModel.status_id,
            )
        ).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.hashed_fingerprint == fingerprint,
            RefreshTokenModel.status_id == TokenStatus.ACTIVE,
            RefreshTokenModel.expires_at > datetime.now(timezone.utc),
        )
        result = await self._session.execute(statement)
        raw_token = result.one_or_none()

        if not raw_token:
            raise

        token = RefreshToken.from_dict(dict(user_id=user_id, **raw_token.refresh_token))
        return token

    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshToken] | None:
        statement = (
            select(
                DictBundle(
                    "refresh_token",
                    RefreshTokenBlacklistModel.hashed_token,
                    RefreshTokenBlacklistModel.expires_at,
                    RefreshTokenBlacklistModel.status_id,
                )
            )
            .where(
                RefreshTokenBlacklistModel.user_id == user_id,
                RefreshTokenBlacklistModel.hashed_fingerprint == fingerprint,
            )
            .order_by(
                RefreshTokenBlacklistModel.status_id,
                RefreshTokenBlacklistModel.expires_at,
            )
        )
        result = await self._session.execute(statement)
        raw_tokens = result.all()

        if not raw_tokens:
            return

        tokens = [
            RefreshToken.from_dict(dict(user_id=user_id, **token_data.refresh_token))
            for token_data in raw_tokens
        ]

        return tokens

    async def _move_older_refresh_token_to_blacklist(
        self, user_id: UUID, fingerprint: str
    ) -> None:
        statement = (
            delete(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.hashed_fingerprint == fingerprint,
            )
            .returning(
                RefreshTokenModel.user_id,
                RefreshTokenModel.hashed_token,
                RefreshTokenModel.hashed_fingerprint,
                RefreshTokenModel.created_at,
                RefreshTokenModel.expires_at,
            )
        )

        try:
            result = await self._session.execute(statement)
            deleted_models = result.all()

            if deleted_models:
                blacklisted_models = []

                for model in deleted_models:
                    if model.expires_at <= datetime.now(timezone.utc):
                        status_id = TokenStatus.REVOKED
                        revoked_at = datetime.now(timezone.utc)
                    else:
                        status_id = TokenStatus.EXPIRED
                        revoked_at = None

                    blacklisted_models.append(
                        RefreshTokenBlacklistModel(
                            user_id=model.user_id,
                            hashed_token=model.hashed_token,
                            hashed_fingerprint=model.hashed_fingerprint,
                            created_at=model.created_at,
                            expires_at=model.expires_at,
                            revoked_at=revoked_at,
                            status_id=status_id,
                        )
                    )
                self._session.add_all(blacklisted_models)

        except Exception as e:
            raise e

    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str) -> None:
        time_revealed = datetime.now(timezone.utc)
        statement = (
            delete(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.hashed_fingerprint == fingerprint,
                RefreshTokenModel.created_at < time_revealed,
            )
            .returning(
                RefreshTokenModel.user_id,
                RefreshTokenModel.hashed_token,
                RefreshTokenModel.hashed_fingerprint,
                RefreshTokenModel.created_at,
                RefreshTokenModel.expires_at,
            )
        )

        try:
            result = await self._session.execute(statement)
            deleted_models = result.all()
            blacklisted_models = []

            for model in deleted_models:
                blacklisted_models.append(
                    RefreshTokenBlacklistModel(
                        user_id=model.user_id,
                        hashed_token=model.hashed_token,
                        hashed_fingerprint=model.hashed_fingerprint,
                        created_at=model.created_at,
                        expires_at=model.expires_at,
                        status_id=TokenStatus.COMPROMISED,
                    )
                )
            self._session.add_all(blacklisted_models)

        except Exception:
            logger.error("Failed to delete compromised tokens")

            statement = (
                update(RefreshTokenModel)
                .where(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.hashed_fingerprint == fingerprint,
                    RefreshTokenModel.created_at < time_revealed,
                )
                .values(status_id=TokenStatus.COMPROMISED)
            )
            await self._session.execute(statement)

        update_statement = (
            update(RefreshTokenBlacklistModel)
            .where(
                RefreshTokenBlacklistModel.user_id == user_id,
                RefreshTokenBlacklistModel.hashed_fingerprint == fingerprint,
            )
            .values(status_id=TokenStatus.COMPROMISED)
        )

        try:
            await self._session.execute(update_statement)

        except Exception:
            logger.error("Failed to mark tokens as compromised")
