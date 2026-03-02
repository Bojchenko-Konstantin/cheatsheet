import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import RefreshTokenRecord, TokenStatus
from src.application.exceptions import (
    RefreshTokenBlacklistAddError,
    RefreshTokenCompromisedMarkError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokeError,
)
from src.application.interfaces.repositories import ITokenRepo
from src.infrastructure.database.models import (
    RefreshTokenBlacklistModel,
    RefreshTokenModel,
)
from src.infrastructure.repositories.utils import DictBundle

logger = logging.getLogger(__name__)


class SQLAlchemyTokenRepo(ITokenRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, token_record: RefreshTokenRecord) -> None:
        await self._move_older_refresh_token_to_blacklist(
            token_record.user_id,
            token_record.hashed_fingerprint,  # type: ignore
        )

        model = RefreshTokenModel(
            user_id=token_record.user_id,
            hashed_token=token_record.hashed_token,
            hashed_fingerprint=token_record.hashed_fingerprint,
            expires_at=token_record.expires_at,
        )
        self._session.add(model)

    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshTokenRecord:
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
            raise RefreshTokenNotFoundError

        token_record = RefreshTokenRecord(user_id=user_id, **raw_token.refresh_token)
        return token_record

    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshTokenRecord] | None:
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
        raw_token_records = result.all()

        if not raw_token_records:
            raise RefreshTokenNotFoundError

        token_records = [
            RefreshTokenRecord(user_id=user_id, **token_data.refresh_token)
            for token_data in raw_token_records
        ]
        return token_records

    async def revoke_token(
        self, user_id: UUID, fingerprint: str, hashed_token: str
    ) -> None:
        try:
            statement = select(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.hashed_fingerprint == fingerprint,
                RefreshTokenModel.hashed_token == hashed_token,
                RefreshTokenModel.status_id == TokenStatus.ACTIVE,
            )
            result = await self._session.execute(statement)
            token_model = result.scalar_one_or_none()

            if not token_model:
                raise RefreshTokenNotFoundError

            await self._session.delete(token_model)

            blacklisted_model = RefreshTokenBlacklistModel(
                user_id=token_model.user_id,
                hashed_token=token_model.hashed_token,
                hashed_fingerprint=token_model.hashed_fingerprint,
                created_at=token_model.created_at,
                expires_at=token_model.expires_at,
                revoked_at=datetime.now(timezone.utc),
                status_id=TokenStatus.REVOKED,
            )
            self._session.add(blacklisted_model)
        except IntegrityError as e:
            raise RefreshTokenRevokeError from e

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
            logger.error("Failed to move refresh token to blacklist")
            raise RefreshTokenBlacklistAddError from e

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
        except Exception as e:
            logger.error("Failed to mark tokens as compromised")
            raise RefreshTokenCompromisedMarkError from e
