from typing import Any
from uuid import UUID

from pwdlib import PasswordHash

from src.application.dto import User, UserPayload
from src.application.interfaces import IUnitOfWork


class UserUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._unit_of_work = unit_of_work

    async def get_by_user_name(self, user_name: str) -> User:
        async with self._unit_of_work as uow:
            user = await uow.user_repo.get_by_user_name(user_name)
            return user

    async def get_by_id(self, user_id: UUID) -> User:
        async with self._unit_of_work as uow:
            user = await uow.user_repo.get_by_id(user_id)
            return user

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        async with self._unit_of_work as uow:
            password = create_data.pop("password")
            del create_data["password_confirmation"]
            create_data["hashed_password"] = self._create_hashed_password(password)
            user = await uow.user_repo.create(create_data)
            return user

    @staticmethod
    def _create_hashed_password(plain_password: str) -> str:
        password_hash = PasswordHash.recommended()
        return password_hash.hash(plain_password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        password_hash = PasswordHash.recommended()
        return password_hash.verify(plain_password, hashed_password)
