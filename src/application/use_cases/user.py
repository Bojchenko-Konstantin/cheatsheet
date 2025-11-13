from src.application.dto import User
from src.application.interfaces import IUnitOfWork


class UserUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._unit_of_work = unit_of_work

    async def get_by_user_name(self, user_name: str) -> User:
        async with self._unit_of_work as uow:
            user = await uow.user_repo.get_by_user_name(user_name)
            return user
