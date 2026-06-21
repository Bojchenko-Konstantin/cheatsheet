import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Row, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import RefreshTokenRecord, TokenStatus
from src.application.exceptions import (
    AddRefreshTokenToBlacklistError,
    MarkRefreshTokenAsCompromisedError,
    RefreshTokenNotFoundError,
    RevokeRefreshTokenError,
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

    async def get_device_active_token(
        self, user_id: UUID, fingerprint: str
    ) -> RefreshTokenRecord:
        """
        Retrieves the current active refresh token record for a specific device.
        Raises RefreshTokenNotFoundError if no active token is found.
        """
        raw_token = await self._fetch_active_token_data(user_id, fingerprint)

        if not raw_token:
            raise RefreshTokenNotFoundError

        token_record = self._map_to_token_record(user_id, raw_token.refresh_token)
        return token_record

    async def get_device_blacklisted_token_family(
        self, user_id: UUID, fingerprint: str
    ) -> list[RefreshTokenRecord]:
        """
        Retrieves the family (history) of blacklisted tokens for a specific device.
        Raises RefreshTokenNotFoundError if no blacklisted tokens exist.
        """
        raw_token_records = await self._fetch_blacklisted_family_data(
            user_id, fingerprint
        )

        if not raw_token_records:
            raise RefreshTokenNotFoundError

        return [
            self._map_to_token_record(user_id, token_data.refresh_token)
            for token_data in raw_token_records
        ]

    async def revoke_token(
        self, user_id: UUID, fingerprint: str, hashed_token: str
    ) -> None:
        """
        Revokes a specific active refresh token and moves it to the blacklist.
        """
        token_model = await self._get_active_refresh_token(
            user_id, fingerprint, hashed_token
        )

        if not token_model:
            raise RefreshTokenNotFoundError

        blacklisted_model = self._map_to_revoked_blacklist_model(token_model)

        try:
            await self._session.delete(token_model)
            self._session.add(blacklisted_model)
        except IntegrityError as e:
            raise RevokeRefreshTokenError from e

    async def revoke_all_tokens_for_user(self, user_id: UUID) -> None:
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

    async def mark_tokens_as_compromised(self, user_id: UUID, fingerprint: str) -> None:
        """
        Marks all active and previously blacklisted tokens for a specific device
        as compromised due to a security breach (e.g., token reuse).
        """
        time_revealed = datetime.now(timezone.utc)

        try:
            async with self._session.begin_nested():
                deleted_models = await self._delete_compromised_tokens(
                    user_id, fingerprint, time_revealed
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
            await self._fallback_update_compromised_tokens(
                user_id, fingerprint, time_revealed
            )

        try:
            await self._update_blacklisted_tokens_status(user_id, fingerprint)
        except Exception as e:
            logger.exception("Failed to mark tokens as compromised")
            raise MarkRefreshTokenAsCompromisedError from e

    async def _fetch_active_token_data(
        self, user_id: UUID, fingerprint: str
    ) -> Row | None:
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
        return result.one_or_none()

    async def _fetch_blacklisted_family_data(
        self, user_id: UUID, fingerprint: str
    ) -> Sequence[Row]:
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
        return result.all()

    async def _get_active_refresh_token(
        self, user_id: UUID, fingerprint: str, hashed_token: str
    ) -> RefreshTokenModel | None:
        statement = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.hashed_fingerprint == fingerprint,
            RefreshTokenModel.hashed_token == hashed_token,
            RefreshTokenModel.status_id == TokenStatus.ACTIVE,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def _move_older_refresh_token_to_blacklist(
        self, user_id: UUID, fingerprint: str
    ) -> None:
        try:
            deleted_models = await self._delete_and_return_old_tokens(
                user_id, fingerprint
            )

            if deleted_models:
                blacklisted_models = self._map_to_blacklist_models(deleted_models)
                self._session.add_all(blacklisted_models)
        except Exception as e:
            logger.exception("Failed to move refresh token to blacklist")
            raise AddRefreshTokenToBlacklistError from e

    async def _delete_and_return_old_tokens(self, user_id: UUID, fingerprint: str):
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

        result = await self._session.execute(statement)
        return result.all()

    async def _delete_compromised_tokens(
        self, user_id: UUID, fingerprint: str, time_revealed: datetime
    ) -> Sequence[Row]:
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
        result = await self._session.execute(statement)
        return result.all()

    async def _fallback_update_compromised_tokens(
        self, user_id: UUID, fingerprint: str, time_revealed: datetime
    ) -> None:
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

    async def _update_blacklisted_tokens_status(
        self, user_id: UUID, fingerprint: str
    ) -> None:
        update_statement = (
            update(RefreshTokenBlacklistModel)
            .where(
                RefreshTokenBlacklistModel.user_id == user_id,
                RefreshTokenBlacklistModel.hashed_fingerprint == fingerprint,
            )
            .values(status_id=TokenStatus.COMPROMISED)
        )

        await self._session.execute(update_statement)

    @staticmethod
    def _map_to_token_record(user_id: UUID, raw_token_dict: dict) -> RefreshTokenRecord:
        return RefreshTokenRecord(user_id=user_id, **raw_token_dict)

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
                status_id = TokenStatus.REVOKED
                revoked_at = current_time
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
