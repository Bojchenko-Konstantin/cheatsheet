from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from domain.entities import Cheatsheet, Tag
from domain.repositories.cheatsheet import (
    AbstractCheatsheetRepository,
)
from infrastructure.database.models.cheatsheet import (
    Cheatsheet as CheatsheetModel,
)
from infrastructure.database.models.cheatsheet_stats import (
    CheatsheetStats as StatsModel,
)
from infrastructure.database.models.tag import Tag as TagModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyCheatsheetRepository(AbstractCheatsheetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: CheatsheetModel) -> Cheatsheet:
        return Cheatsheet(
            cheatsheet_id=model.cheatsheet_id,
            title=model.title,
            content=model.content,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_public=model.is_public,
            count_like=model.stats.count_like if model.stats else 0,
            count_view=model.stats.count_view if model.stats else 0,
            tags=[
                Tag(tag_id=tag.tag_id, tag_name=tag.tag_name)
                for tag in model.tags
            ],
        )

    def _to_model(self, entity: Cheatsheet) -> CheatsheetModel:
        return CheatsheetModel(
            cheatsheet_id=entity.cheatsheet_id,
            title=entity.title,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_public=entity.is_public,
            tags=[
                TagModel(tag_id=tag.tag_id, tag_name=tag.tag_name)
                for tag in (entity.tags or [])
            ],
            stats=StatsModel(
                count_like=entity.count_like,
                count_view=entity.count_view,
                cheatsheet_id=entity.cheatsheet_id,
            ),
        )

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

        return self._to_entity(model) if model else None

    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        model = self._to_model(cheatsheet)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, ["tags", "stats"])
        return self._to_entity(model)
