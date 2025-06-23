from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from domain.entities import Cheatsheet, Tag
from domain.repositories.cheatsheet_repository import (
    AbstractCheatsheetRepository,
)
from infrastructure.database.models.cheatsheet import (
    Cheatsheet as CheatsheetModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyCheatsheetRepository(AbstractCheatsheetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, cheatsheet_id: int) -> Cheatsheet | None:
        statement = (
            select(CheatsheetModel)
            .where(CheatsheetModel.cheatsheet_id == cheatsheet_id)
            .options(
                selectinload(CheatsheetModel.tags),
                joinedload(CheatsheetModel.stats),
            )
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Cheatsheet(
            cheatsheet_id=model.cheatsheet_id,
            title=model.title,
            content=model.content,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_public=model.is_public,
            tags=[
                Tag(tag_id=tag.tag_id, tag_name=tag.tag_name)
                for tag in model.tags
            ],
            count_like=model.stats.count_like if model.stats else 0,
            count_view=model.stats.count_view if model.stats else 0,
        )

    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        model = CheatsheetModel(
            cheatsheet_id=cheatsheet.cheatsheet_id,
            title=cheatsheet.title,
            content=cheatsheet.content,
            is_public=cheatsheet.is_public,
            count_like=cheatsheet.count_like,
            count_view=cheatsheet.count_view,
        )
        self._session.add(model)
        await self._session.flush()
        return cheatsheet
