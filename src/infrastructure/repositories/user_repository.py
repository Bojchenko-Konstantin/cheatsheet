import logging
from collections.abc import MutableMapping
from typing import Any
from uuid import UUID

from sqlalchemy import CursorResult, Row, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import PasswordResetData, User, UserPayload
from src.application.exceptions import (
    DuplicateUserError,
    UserCreationError,
    UserNotFoundError,
)
from src.application.interfaces.repositories import IUserRepo
from src.infrastructure.database.models import UserModel
from src.infrastructure.database.models.registered_user import RegisteredUserModel
from src.infrastructure.database.models.user_detail import UserDetailModel
from src.infrastructure.repositories.utils import DictBundle

logger = logging.getLogger(__name__)


class SQLAlchemyUserRepo(IUserRepo):
    """
    Class for operations with users that interact with database using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user_name(self, user_name: str) -> User:
        model = await self._get_user_model_by_user_name(user_name)

        if not model:
            raise UserNotFoundError

        user = User(**model.user)
        return user

    async def get_by_email(self, email: str) -> User:
        model = await self._get_user_model_by_email(email)

        if not model:
            raise UserNotFoundError

        user = User(**model.user)
        return user

    async def get_by_id(self, user_id: UUID) -> User:
        model = await self._get_user_model_by_id(user_id)

        if not model:
            raise UserNotFoundError

        user = User(**model.user)
        return user

    async def get_password_reset_data(self, email: str) -> PasswordResetData:
        model = await self._get_user_model_for_password_reset(email)

        if not model:
            raise UserNotFoundError

        user = PasswordResetData(**model.user)
        return user

    async def get_email_by_id(self, user_id: UUID) -> str:
        """Get user email by user ID."""
        email = await self._get_user_email_by_id(user_id)

        if not email:
            raise UserNotFoundError

        return email

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        # TODO: add them to the user detail table
        social_network_id = create_data.pop("social_network_id")  # noqa: F841
        network_url = create_data.pop("network_url")  # noqa: F841

        model = self._to_model(create_data)

        try:
            self._session.add(model)
            await self._session.flush()
        except IntegrityError as e:
            if "uq_user_user_name" in str(e) or "uq_user_email" in str(e):
                raise DuplicateUserError from e
            else:
                raise UserCreationError from e
        except Exception as e:
            raise UserCreationError from e

        return UserPayload.create(model.user_id, model.is_superuser)

    async def update(self, update_data: dict[str, Any]):
        pass

    async def update_password(self, user_id: UUID, hashed_password: str) -> None:
        result = await self._update_user_password(user_id, hashed_password)

        if result.rowcount == 0:
            raise UserNotFoundError

    async def mark_email_as_verified(self, user_id: UUID) -> None:
        """Mark user's email as verified in database."""
        statement = (
            update(RegisteredUserModel)
            .where(RegisteredUserModel.user_id == user_id)
            .values(is_verified=True)
        )
        await self._session.execute(statement)

    async def _get_user_model_by_user_name(self, user_name: str) -> Row | None:
        statement = (
            select(
                DictBundle(
                    "user",
                    UserModel.user_id,
                    UserModel.user_name,
                    RegisteredUserModel.hashed_password,
                    UserModel.is_active,
                    UserModel.is_superuser,
                    UserModel.is_verified,
                )
            )
            .join(RegisteredUserModel)
            .where(UserModel.user_name == user_name)
        )
        result = await self._session.execute(statement)
        return result.one_or_none()

    async def _get_user_model_by_email(self, email: str) -> Row | None:
        statement = (
            select(
                DictBundle(
                    "user",
                    UserModel.user_id,
                    UserModel.user_name,
                    RegisteredUserModel.hashed_password,
                    UserModel.is_active,
                    UserModel.is_superuser,
                    UserModel.is_verified,
                )
            )
            .join(RegisteredUserModel)
            .where(UserModel.email == email)
        )
        result = await self._session.execute(statement)
        return result.one_or_none()

    async def _get_user_model_by_id(self, user_id: UUID) -> Row | None:
        statement = (
            select(
                DictBundle(
                    "user",
                    UserModel.user_id,
                    UserModel.user_name,
                    RegisteredUserModel.hashed_password,
                    UserModel.is_active,
                    UserModel.is_superuser,
                    UserModel.is_verified,
                )
            )
            .outerjoin(RegisteredUserModel)
            .where(UserModel.user_id == user_id)
        )
        result = await self._session.execute(statement)
        return result.one_or_none()

    async def _get_user_model_for_password_reset(self, email: str) -> Row | None:
        statement = select(
            DictBundle(
                "user",
                UserModel.user_id,
                UserModel.user_name,
                UserModel.email,
            )
        ).where(UserModel.email == email)
        result = await self._session.execute(statement)
        return result.one_or_none()

    async def _get_user_email_by_id(self, user_id: UUID) -> str | None:
        statement = select(UserModel.email).where(UserModel.user_id == user_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def _update_user_password(
        self, user_id: UUID, hashed_password: str
    ) -> CursorResult:
        statement = (
            update(RegisteredUserModel)
            .where(RegisteredUserModel.user_id == user_id)
            .values(hashed_password=hashed_password)
        )
        return await self._session.execute(statement)

    @staticmethod
    def _to_model(user: MutableMapping[str, Any]) -> UserModel:
        user_copy = dict(user)

        user_name = user_copy.pop("username")

        registered_user = dict(
            hashed_password=user_copy.pop("hashed_password"),
        )
        user_detail = dict(
            first_name=user_copy.pop("first_name"),
            last_name=user_copy.pop("last_name"),
            profile_description=user_copy.pop("profile_description", None),
            image_url=user_copy.pop("image_url", None),
        )

        model = UserModel(**user_copy, user_name=user_name)
        model.detail = UserDetailModel(**user_detail)
        model.registered_user = RegisteredUserModel(**registered_user)
        return model
