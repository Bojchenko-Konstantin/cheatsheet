from typing import Any
from uuid import UUID

from pwdlib import PasswordHash

from src.application.dto import PasswordResetData, User, UserPayload
from src.application.exceptions import (
    EmailAlreadyVerifiedError,
    UserAuthenticationError,
    UserInactiveError,
    UserNotFoundError,
)
from src.application.interfaces import IUnitOfWork, IUserService
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.hasher import HASHER


class UserService(IUserService):
    def __init__(
        self,
        hasher: PasswordHash = HASHER,
        unit_of_work: IUnitOfWork = SQLAlchemyUnitOfWork(),
    ):
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

    async def get_by_email(self, email: str) -> PasswordResetData | None:
        try:
            async with self._unit_of_work.readonly() as uow:
                user = await uow.user_repo.get_by_email(email)
                return user
        except UserNotFoundError:
            return None

    async def get_email_by_id(self, user_id: UUID) -> str:
        async with self._unit_of_work.readonly() as uow:
            return await uow.user_repo.get_email_by_id(user_id)

    async def create(self, create_data: dict[str, Any]) -> UserPayload:
        async with self._unit_of_work as uow:
            del create_data["password_confirmation"]
            password = create_data.pop("password")
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

    async def update_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        user = await self.get_by_id(user_id)
        if not self._verify_password(old_password, user.hashed_password):
            raise UserAuthenticationError

        new_hashed_password = self._create_hashed_password(new_password)

        async with self._unit_of_work as uow:
            await uow.user_repo.update_password(user_id, new_hashed_password)

    async def reset_password(self, user_id: UUID, new_password: str) -> None:
        new_hashed_password = self._create_hashed_password(new_password)

        async with self._unit_of_work as uow:
            await uow.user_repo.update_password(user_id, new_hashed_password)

    async def verify_email(self, user_id: UUID) -> None:
        """Mark user's email as verified in database."""
        async with self._unit_of_work as uow:
            user = await uow.user_repo.get_by_id(user_id)

            if user.is_verified:
                raise EmailAlreadyVerifiedError

            await uow.user_repo.mark_email_as_verified(user_id)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._hasher.verify(plain_password, hashed_password)

    def _create_hashed_password(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)
