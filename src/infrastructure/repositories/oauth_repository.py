import dataclasses
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
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
from src.infrastructure.exceptions.oauth import OAuthAccountCreationError
from src.infrastructure.repositories.utils import DictBundle


class SQLAlchemyOAuthRepo:
    """Class for operations with OAuth that interact with database using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(
        self, refresh_token_hash: str, save_data: OAuthUserCreationData
    ) -> UUID:
        model = self._build_model(refresh_token_hash, save_data)
        self._session.add(model)

        try:
            async with self._session.begin_nested():
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

                return model.user_id
            else:
                raise OAuthAccountCreationError from e
        except Exception as e:
            raise OAuthAccountCreationError from e

    async def get_by_email(self, email: str) -> list[OAuthUserAccount] | None:
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
        model = result.all()

        if not model:
            return None

        accounts = []

        for account in model:
            accounts.append(OAuthUserAccount(**account.oauth_account))

        return accounts

    async def update_refresh_token(
        self,
        oauth_account_id: UUID,
        refresh_token_hash: str,
    ):
        await self._revoke_old_refresh_token(oauth_account_id)

        model = OAuthRefreshTokenModel(
            oauth_account_id=oauth_account_id, hashed_token=refresh_token_hash
        )
        self._session.add(model)

    async def link_new_service(
        self, user_id: UUID, refresh_token_hash: str, save_data: OAuthUserCreationData
    ):
        model = OAuthAccountModel(
            user_id=user_id,
            provider_user_id=save_data.provider_user_id,
            provider_psuid=save_data.provider_psuid,
            oauth_service_id=save_data.oauth_service_id,
        )
        refresh_token = OAuthRefreshTokenModel(hashed_token=refresh_token_hash)
        model.refresh_tokens.append(refresh_token)

        self._session.add(model)

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
