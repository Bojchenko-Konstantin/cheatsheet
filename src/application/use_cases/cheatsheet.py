from typing import Any
from uuid import UUID

from src.application.dto import CheatsheetList, CheatsheetSearchSuggestions
from src.application.interfaces import IUnitOfWork
from src.application.interfaces.services import ICheatsheetSearchService
from src.domain.entities import Cheatsheet


class CheatsheetUseCase:
    def __init__(
        self,
        unit_of_work: IUnitOfWork,
        search_service: ICheatsheetSearchService,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._search_service = search_service

    async def get_by_id(
        self, cheatsheet_id: UUID, current_user_id: UUID | None = None
    ) -> Cheatsheet:
        async with self._unit_of_work.readonly() as uow:
            cheatsheet = await uow.cheatsheet_repo.get_by_id(cheatsheet_id)
            cheatsheet.ensure_accessible_by(current_user_id)
            return cheatsheet

    async def create(self, create_data: dict[str, Any]) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.create(create_data)
            return cheatsheet

    async def update(self, update_data: dict[str, Any]) -> Cheatsheet:
        async with self._unit_of_work as uow:
            cheatsheet = await uow.cheatsheet_repo.update(update_data)
            return cheatsheet

    async def get_cheatsheet_list(
        self,
        user_id: UUID | None,
        cursor: str | None,
        size: int,
        tag: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
    ) -> CheatsheetList:
        self._search_service.validate_search_query(search)
        self._search_service.validate_sort_params(sort_by, sort_order)

        async with self._unit_of_work.readonly() as uow:
            return await uow.cheatsheet_repo.list_accessible_cheatsheets(
                user_id=user_id,
                cursor=cursor,
                size=size,
                tag=tag,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
            )

    async def get_search_suggestions(
        self, query: str, limit: int = 5
    ) -> CheatsheetSearchSuggestions:
        self._search_service.validate_suggestions_limit(limit)

        async with self._unit_of_work.readonly() as uow:
            return await uow.cheatsheet_repo.search_suggestions(
                query=query,
                limit=limit,
            )
