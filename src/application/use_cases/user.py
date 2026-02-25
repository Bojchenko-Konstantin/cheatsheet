from typing import Any
from uuid import UUID

from pwdlib import PasswordHash

from src.application.dto import User, UserPayload
from src.application.exceptions import (
    UserAuthenticationError,
    UserInactiveError,
    UserNotFoundError,
)
from src.application.hasher import HASHER
from src.application.interfaces import IUnitOfWork


class UserUseCase:
    def __init__(self, unit_of_work: IUnitOfWork, hasher: PasswordHash = HASHER):
        self._unit_of_work = unit_of_work
        self._hasher = hasher

    async def get_by_user_name(self, user_name: str) -> User:
        async with self._unit_of_work.readonly() as uow:
            user = await uow.user_repo.get_by_user_name(user_name)
            return user

    async def get_by_id(self, user_id: UUID) -> User:
        async with self._unit_of_work.readonly() as uow:
            user = await uow.user_repo.get_by_id(user_id)
            return user

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        async with self._unit_of_work as uow:
            password = create_data.pop("password")
            del create_data["password_confirmation"]
            create_data["hashed_password"] = self._create_hashed_password(password)
            user_payload = await uow.user_repo.create(create_data)
            return user_payload

    async def authenticate_user(self, user_name: str, password: str) -> User:
        try:
            user = await self.get_by_user_name(user_name)

        except UserNotFoundError:
            raise

        if not self._verify_password(password, user.hashed_password):
            raise UserAuthenticationError

        if not user.is_active:
            raise UserInactiveError

        return user

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._hasher.verify(plain_password, hashed_password)

    def _create_hashed_password(self, plain_password: str) -> str:
        password_hash = self._hasher.hash(plain_password)
        return password_hash
