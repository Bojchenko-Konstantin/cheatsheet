import dataclasses
import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Row, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.token import TokenStatus
from src.infrastructure.database.models import (
    OAuthAccountModel,
    OAuthRefreshTokenModel,
    OAuthServiceModel,
    UserModel,
)
from src.infrastructure.dto import OAuthUserAccount, OAuthUserCreationData
from src.infrastructure.exceptions.oauth import (
    OAuthAccountCreationError,
    OAuthServiceLinkageError,
    OAuthTokenRotationError,
)
from src.infrastructure.repositories.utils import DictBundle

logger = logging.getLogger(__name__)


class SQLAlchemyOAuthRepo:
    """Class for operations with OAuth that interact with database using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(
        self, refresh_token_hash: str, save_data: OAuthUserCreationData
    ) -> UUID:
        model = self._build_model(refresh_token_hash, save_data)

        try:
            async with self._session.begin_nested():
                self._session.add(model)
                await self._session.flush()
                return model.user_id
        except IntegrityError as e:
            if "uq_user_user_name" in str(e):
                timestamp_suffix = str(int(datetime.now(timezone.utc).timestamp()))
                save_data = dataclasses.replace(
                    save_data, user_name=f"{save_data.user_name}_{timestamp_suffix}"
                )

                new_model = self._build_model(refresh_token_hash, save_data)

                self._session.add(new_model)
                await self._session.flush()

                return new_model.user_id
            else:
                raise OAuthAccountCreationError from e
        except Exception as e:
            raise OAuthAccountCreationError from e

    async def get_by_email(self, email: str) -> list[OAuthUserAccount] | None:
        model = await self._get_oauth_account_model_by_email(email)

        if not model:
            return None

        return [OAuthUserAccount(**account.oauth_account) for account in model]

    async def update_refresh_token(
        self,
        oauth_account_id: UUID,
        refresh_token_hash: str,
    ):
        try:
            await self._revoke_old_refresh_token(oauth_account_id)
            await self._save_new_refresh_token(oauth_account_id, refresh_token_hash)
            await self._session.flush()
        except Exception as e:
            logger.exception("Failed to rotate OAuth refresh token")
            raise OAuthTokenRotationError from e

    async def link_new_service(
        self, user_id: UUID, refresh_token_hash: str, save_data: OAuthUserCreationData
    ):
        try:
            model = OAuthAccountModel(
                user_id=user_id,
                provider_user_id=save_data.provider_user_id,
                provider_psuid=save_data.provider_psuid,
                oauth_service_id=save_data.oauth_service_id,
            )
            refresh_token = OAuthRefreshTokenModel(hashed_token=refresh_token_hash)
            model.refresh_tokens.append(refresh_token)

            self._session.add(model)
            await self._session.flush()
        except Exception as e:
            raise OAuthServiceLinkageError from e

    def _build_model(
        self, refresh_token_hash: str, save_data: OAuthUserCreationData
    ) -> UserModel:
        model = UserModel(user_name=save_data.user_name, email=save_data.email)

        # TODO: save user detail

        model.oauth_account = OAuthAccountModel(
            provider_user_id=save_data.provider_user_id,
            provider_psuid=save_data.provider_psuid,
            oauth_service_id=save_data.oauth_service_id,
        )

        refresh_token = OAuthRefreshTokenModel(hashed_token=refresh_token_hash)
        model.oauth_account.refresh_tokens.append(refresh_token)
        return model

    async def _revoke_old_refresh_token(self, oauth_account_id: UUID) -> None:
        stmt = (
            update(OAuthRefreshTokenModel)
            .where(
                OAuthRefreshTokenModel.oauth_account_id == oauth_account_id,
                OAuthRefreshTokenModel.status_id == TokenStatus.ACTIVE,
            )
            .values(status_id=TokenStatus.REVOKED)
        )
        await self._session.execute(stmt)

    async def _get_oauth_account_model_by_email(self, email: str) -> Sequence[Row]:
        statement = (
            select(
                DictBundle(
                    "oauth_account",
                    OAuthAccountModel.oauth_account_id,
                    OAuthAccountModel.oauth_service_id,
                    OAuthServiceModel.oauth_service_name,
                    UserModel.user_id,
                    UserModel.user_name,
                    UserModel.email,
                )
            )
            .join(UserModel)
            .join(OAuthServiceModel)
            .where(UserModel.email == email)
        )
        result = await self._session.execute(statement)
        return result.all()

    async def _save_new_refresh_token(
        self, oauth_account_id: UUID, refresh_token_hash: str
    ) -> None:
        model = OAuthRefreshTokenModel(
            oauth_account_id=oauth_account_id, hashed_token=refresh_token_hash
        )
        self._session.add(model)
