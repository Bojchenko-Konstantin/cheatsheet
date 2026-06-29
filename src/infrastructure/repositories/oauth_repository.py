import dataclasses
import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Row, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import (
    OAuthAccountModel,
    OAuthServiceModel,
    RegisteredUserModel,
    UserModel,
)
from src.infrastructure.dto import (
    OAuthAccountLinkingData,
    OAuthService,
    OAuthUserAccount,
    OAuthUserCreationData,
)
from src.infrastructure.exceptions.oauth import (
    OAuthAccountCreationError,
    OAuthServiceLinkageError,
)
from src.infrastructure.repositories.utils import DictBundle

logger = logging.getLogger(__name__)


class SQLAlchemyOAuthRepo:
    """Class for operations with OAuth that interact with database using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, save_data: OAuthUserCreationData) -> UUID:
        model = self._to_model(save_data)

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

                new_model = self._to_model(save_data)

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

    async def link_new_service(self, user_id: UUID, save_data: OAuthAccountLinkingData):
        try:
            model = OAuthAccountModel(
                user_id=user_id,
                provider_user_id=save_data.provider_user_id,
                provider_psuid=save_data.provider_psuid,
                oauth_service_id=save_data.oauth_service_id,
            )

            self._session.add(model)
            await self._session.flush()
        except Exception as e:
            raise OAuthServiceLinkageError from e

    async def get_user_with_oauth_accounts(
        self, user_id: UUID
    ) -> tuple[str | None, int]:
        statement = (
            select(
                DictBundle(
                    "account",
                    RegisteredUserModel.hashed_password,
                    func.count(OAuthAccountModel.oauth_account_id).label(
                        "account_count"
                    ),
                ),
            )
            .select_from(UserModel)
            .outerjoin(RegisteredUserModel)
            .outerjoin(OAuthAccountModel)
            .where(UserModel.user_id == user_id)
            .group_by(RegisteredUserModel.hashed_password)
        )
        result = await self._session.execute(statement)
        db_row = result.one()
        return db_row.account["hashed_password"], db_row.account["account_count"]

    async def unlink_account(self, user_id: UUID, oauth_service_id: OAuthService):
        statement = delete(OAuthAccountModel).where(
            OAuthAccountModel.user_id == user_id,
            OAuthAccountModel.oauth_service_id == oauth_service_id,
        )
        await self._session.execute(statement)

    def _to_model(self, save_data: OAuthUserCreationData) -> UserModel:
        model = UserModel(user_name=save_data.user_name, email=save_data.email)

        # TODO: save user detail

        oauth_account_model = OAuthAccountModel(
            provider_user_id=save_data.provider_user_id,
            provider_psuid=save_data.provider_psuid,
            oauth_service_id=save_data.oauth_service_id,
        )
        model.oauth_accounts.append(oauth_account_model)

        return model

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
