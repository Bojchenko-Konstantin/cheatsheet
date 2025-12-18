from typing import Any
from uuid import UUID

from src.application.exceptions import CheatsheetAccessDeniedError
from src.application.interfaces import IUnitOfWork
from src.domain.entities import Cheatsheet


class CheatsheetUseCase:
    def __init__(self, unit_of_work: IUnitOfWork):
        self._unit_of_work = unit_of_work

    async def get_by_id(
        self, cheatsheet_id: UUID, current_user_id: UUID | None = None
    ) -> Cheatsheet:
        async with self._unit_of_work.readonly() as uow:
            cheatsheet = await uow.cheatsheet_repo.get_by_id(cheatsheet_id)

            if not cheatsheet.is_public and (
                not current_user_id or cheatsheet.user_id != current_user_id
            ):
                raise CheatsheetAccessDeniedError(
                    f"Access denied to cheatsheet {cheatsheet_id}"
                )

            return cheatsheet

    async def create(self, create_data: dict[str, Any]) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.create(create_data)
            return cheatsheet

    async def update(self, update_data: dict[str, Any]) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.update(update_data)
            return cheatsheet
