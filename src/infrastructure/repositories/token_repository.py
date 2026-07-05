import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Row, delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import RefreshTokenRecord, TokenStatus, UserPayload
from src.application.exceptions import (
    AddRefreshTokenToBlacklistError,
    MarkRefreshTokenAsCompromisedError,
    RefreshTokenNotFoundError,
    RevokeRefreshTokenError,
)
from src.application.interfaces import ITokenRepo
from src.infrastructure.database.models import (
    RefreshTokenBlacklistModel,
    RefreshTokenModel,
    UserModel,
)

logger = logging.getLogger(__name__)


class SQLAlchemyTokenRepo(ITokenRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, token_record: RefreshTokenRecord) -> None:
        """
        Saves a new active refresh token and blacklists the older one
        for the specified device (fingerprint).
        """
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

    async def get_user_payload_by_hash(
        self, hashed_token: str, hashed_fingerprint: str
    ) -> UserPayload | None:
        raw_token = await self._fetch_user_data(hashed_token, hashed_fingerprint)

        if not raw_token:
            return None

        return UserPayload(
            user_id=raw_token.user_id, is_superuser=raw_token.is_superuser
        )

    async def is_token_in_blacklist(self, hashed_token: str) -> bool:
        """
        Checks if received token is in the blacklisted family for a specific device.
        """
        statement = select(
            exists().where(RefreshTokenBlacklistModel.hashed_token == hashed_token)
        )
        return await self._session.scalar(statement) or False

    async def revoke_token(self, hashed_token: str, hashed_fingerprint: str) -> None:
        """
        Revokes active refresh token for a specific device
        and moves it to the blacklist.
        """
        token_model = await self._fetch_active_refresh_token_model(
            hashed_token, hashed_fingerprint
        )

        if not token_model:
            raise RefreshTokenNotFoundError

        blacklisted_model = self._map_to_revoked_blacklist_model(token_model)

        try:
            async with self._session.begin_nested():
                await self._session.delete(token_model)
                self._session.add(blacklisted_model)
        except Exception:
            try:
                await self._fallback_set_token_revoked(token_model.user_id)
            except Exception as e:
                raise RevokeRefreshTokenError from e

    async def revoke_all_tokens(self, user_id: UUID) -> None:
        """
        Revokes all active refresh tokens for a given user across all devices.
        Note: This updates tokens in place and does not move them to the blacklist.
        """
        statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.status_id == TokenStatus.ACTIVE,
            )
            .values(status_id=TokenStatus.REVOKED)
        )
        await self._session.execute(statement)

    async def mark_as_compromised(self, hashed_token: str) -> None:
        """
        Marks all active and previously blacklisted tokens for a specific device
        as compromised due to a security breach (e.g. token reuse).
        """
        time_revealed = datetime.now(timezone.utc)
        user_id = await self._get_user_id_by_blacklisted_hash(hashed_token)

        try:
            async with self._session.begin_nested():
                await self._delete_active_tokens_with_fallback(user_id, time_revealed)

                await self._update_blacklisted_tokens_status(user_id)
        except Exception as e:
            logger.exception("Failed to mark tokens as compromised")
            raise MarkRefreshTokenAsCompromisedError from e

    async def _fallback_set_token_revoked(self, user_id: UUID) -> None:
        statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.status_id == TokenStatus.ACTIVE,
            )
            .values(status_id=TokenStatus.REVOKED)
        )
        await self._session.execute(statement)

    async def _delete_active_tokens_with_fallback(
        self, user_id: UUID, time_revealed: datetime
    ) -> None:
        """
        Attempts to delete compromised tokens and move them to the blacklist.
        If a DB error occurs, falls back to a simple status update.
        """
        try:
            async with self._session.begin_nested():
                deleted_models = await self._delete_compromised_tokens(
                    user_id, time_revealed
                )

                if deleted_models:
                    blacklisted_models = self._map_to_compromised_blacklist_models(
                        deleted_models
                    )
                    self._session.add_all(blacklisted_models)

        except Exception:
            logger.exception(
                "Failed to delete compromised tokens, falling back to update"
            )
            await self._fallback_set_tokens_compromised(user_id, time_revealed)

    async def _get_user_id_by_blacklisted_hash(self, hashed_token: str) -> UUID:
        statement = select(
            RefreshTokenBlacklistModel.user_id,
        ).where(
            RefreshTokenBlacklistModel.hashed_token == hashed_token,
        )
        result = await self._session.execute(statement)
        db_row = result.one_or_none()

        if db_row is None:
            raise RefreshTokenNotFoundError

        return db_row.user_id

    async def _fetch_active_refresh_token_model(
        self, hashed_token: str, hashed_fingerprint: str
    ) -> RefreshTokenModel | None:
        statement = select(RefreshTokenModel).where(
            RefreshTokenModel.hashed_token == hashed_token,
            RefreshTokenModel.hashed_fingerprint == hashed_fingerprint,
            RefreshTokenModel.status_id == TokenStatus.ACTIVE,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def _fetch_user_data(
        self, hashed_token: str, hashed_fingerprint: str
    ) -> Row | None:
        statement = (
            select(
                UserModel.user_id,
                UserModel.is_superuser,
            )
            .select_from(RefreshTokenModel)
            .join(UserModel)
            .where(
                RefreshTokenModel.hashed_token == hashed_token,
                RefreshTokenModel.hashed_fingerprint == hashed_fingerprint,
                RefreshTokenModel.status_id == TokenStatus.ACTIVE,
                RefreshTokenModel.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self._session.execute(statement)
        return result.one_or_none()

    async def _move_older_refresh_token_to_blacklist(
        self, user_id: UUID, hashed_fingerprint: str
    ) -> None:
        try:
            deleted_models = await self._delete_and_return_old_tokens(
                user_id, hashed_fingerprint
            )

            if deleted_models:
                blacklisted_models = self._map_to_blacklist_models(deleted_models)
                self._session.add_all(blacklisted_models)
        except Exception as e:
            logger.exception("Failed to move refresh token to blacklist")
            raise AddRefreshTokenToBlacklistError from e

    async def _delete_and_return_old_tokens(
        self, user_id: UUID, hashed_fingerprint: str
    ):
        statement = (
            delete(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.hashed_fingerprint == hashed_fingerprint,
            )
            .returning(
                RefreshTokenModel.user_id,
                RefreshTokenModel.hashed_token,
                RefreshTokenModel.hashed_fingerprint,
                RefreshTokenModel.created_at,
                RefreshTokenModel.expires_at,
            )
        )

        result = await self._session.execute(statement)
        return result.all()

    async def _delete_compromised_tokens(
        self, user_id: UUID, time_revealed: datetime
    ) -> Sequence[Row]:
        statement = (
            delete(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
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
        result = await self._session.execute(statement)
        return result.all()

    async def _fallback_set_tokens_compromised(
        self, user_id: UUID, time_revealed: datetime
    ) -> None:
        statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.created_at < time_revealed,
            )
            .values(status_id=TokenStatus.COMPROMISED)
        )
        await self._session.execute(statement)

    async def _update_blacklisted_tokens_status(self, user_id: UUID) -> None:
        update_statement = (
            update(RefreshTokenBlacklistModel)
            .where(
                RefreshTokenBlacklistModel.user_id == user_id,
            )
            .values(status_id=TokenStatus.COMPROMISED)
        )

        await self._session.execute(update_statement)

    @staticmethod
    def _map_to_revoked_blacklist_model(
        token_model: RefreshTokenModel,
    ) -> RefreshTokenBlacklistModel:
        return RefreshTokenBlacklistModel(
            user_id=token_model.user_id,
            hashed_token=token_model.hashed_token,
            hashed_fingerprint=token_model.hashed_fingerprint,
            created_at=token_model.created_at,
            expires_at=token_model.expires_at,
            revoked_at=datetime.now(timezone.utc),
            status_id=TokenStatus.REVOKED,
        )

    @staticmethod
    def _map_to_blacklist_models(
        deleted_models: Sequence[Row],
    ) -> list[RefreshTokenBlacklistModel]:
        blacklisted_models = []
        current_time = datetime.now(timezone.utc)

        for model in deleted_models:
            if model.expires_at <= current_time:
                status_id = TokenStatus.EXPIRED
                revoked_at = current_time
            else:
                status_id = TokenStatus.REVOKED
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

        return blacklisted_models

    @staticmethod
    def _map_to_compromised_blacklist_models(
        deleted_models: Sequence[Row],
    ) -> list[RefreshTokenBlacklistModel]:
        return [
            RefreshTokenBlacklistModel(
                user_id=model.user_id,
                hashed_token=model.hashed_token,
                hashed_fingerprint=model.hashed_fingerprint,
                created_at=model.created_at,
                expires_at=model.expires_at,
                status_id=TokenStatus.COMPROMISED,
            )
            for model in deleted_models
        ]
