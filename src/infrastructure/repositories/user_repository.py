from collections.abc import MutableMapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.user import IUserRepo
from src.infrastructure.database.models import (
    UserModel,
)
from src.infrastructure.repositories.utils import DictBundle


class SQLAlchemyUserRepo(IUserRepo):
    """
    Class for operations with users that interact with database using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_model(self, user: MutableMapping[str, Any]) -> UserModel:
        pass

    async def get_by_user_name(self, user_name: str):
        statement = (
            select(
                DictBundle(
                    "user",
                    UserModel.user_id,
                    UserModel.user_name,
                    UserModel.hashed_password,
                    UserModel.is_active,
                    UserModel.is_superuser,
                    UserModel.is_verified,
                ),
            )
            # .join(UserModel.detail)
            .where(UserModel.user_name == user_name)
        )
        result = await self._session.execute(statement)
        model = result.one_or_none()
        print(model)

        if not model:
            raise

        user = model.user
        return user

    async def create(self, create_data: dict[str, Any]):
        pass

    async def update(self, update_data: dict[str, Any]):
        pass
