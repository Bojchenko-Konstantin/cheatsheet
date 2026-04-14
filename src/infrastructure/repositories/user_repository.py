import logging
from collections.abc import MutableMapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import User, UserPayload
from src.application.exceptions import (
    DuplicateUserError,
    UserCreationError,
    UserNotFoundError,
)
from src.application.interfaces.repositories import IUserRepo
from src.infrastructure.database.models import UserModel
from src.infrastructure.database.models.user_detail import UserDetailModel
from src.infrastructure.repositories.utils import DictBundle

logger = logging.getLogger(__name__)


class SQLAlchemyUserRepo(IUserRepo):
    """
    Class for operations with users that interact with database using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_model(self, user: MutableMapping[str, Any]) -> UserModel:
        user_name = user.pop("username")
        user_detail = dict(
            user_id=user.pop("user_id", None),
            first_name=user.pop("first_name"),
            last_name=user.pop("last_name"),
            profile_description=user.pop("profile_description"),
            image_url=user.pop("image_url"),
        )

        model = UserModel(**user, user_name=user_name)
        model.detail = UserDetailModel(**user_detail)
        return model

    async def get_by_user_name(self, user_name: str) -> User:
        statement = select(
            DictBundle(
                "user",
                UserModel.user_id,
                UserModel.user_name,
                UserModel.hashed_password,
                UserModel.is_active,
                UserModel.is_superuser,
                UserModel.is_verified,
            )
        ).where(UserModel.user_name == user_name)
        result = await self._session.execute(statement)
        model = result.one_or_none()

        if not model:
            raise UserNotFoundError

        user = User(**model.user)
        return user

    async def get_by_id(self, user_id: UUID) -> User:
        statement = select(
            DictBundle(
                "user",
                UserModel.user_id,
                UserModel.user_name,
                UserModel.hashed_password,
                UserModel.is_active,
                UserModel.is_superuser,
                UserModel.is_verified,
            )
        ).where(UserModel.user_id == user_id)
        result = await self._session.execute(statement)
        model = result.one_or_none()

        if not model:
            raise UserNotFoundError

        user = User(**model.user)
        return user

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        # TODO: add them to the user detail table
        social_network_id = create_data.pop("social_network_id")  # noqa: F841
        network_url = create_data.pop("network_url")  # noqa: F841

        model = self._to_model(create_data)

        try:
            self._session.add(model)
            await self._session.flush()
        except IntegrityError as e:
            if "uq_user_user_name" in str(e):
                raise DuplicateUserError from e
            else:
                raise UserCreationError from e
        except Exception as e:
            raise UserCreationError from e

        return UserPayload.create(model.user_id, model.is_superuser)

    async def update(self, update_data: dict[str, Any]):
        pass
