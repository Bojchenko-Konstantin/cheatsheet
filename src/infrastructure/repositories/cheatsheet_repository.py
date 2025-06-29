from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from domain.entities import Cheatsheet, Tag
from domain.repositories.cheatsheet import ICheatsheetRepo
from infrastructure.database.models.cheatsheet import (
    Cheatsheet as CheatsheetModel,
)
from infrastructure.database.models.cheatsheet_stats import (
    CheatsheetStats as StatsModel,
)
from infrastructure.database.models.cheatsheet_to_tag import (
    CheatsheetToTag as CheatsheetToTagModel,
)
from infrastructure.database.models.tag import Tag as TagModel


class SQLAlchemyCheatsheetRepository(ICheatsheetRepo):
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
            tags=[
                Tag(
                    tag_id=tag_assoc.tag.tag_id,
                    tag_name=tag_assoc.tag.tag_name,
                )
                for tag_assoc in model.tags_association
            ],
            count_like=model.stats.count_like if model.stats else 0,
            count_view=model.stats.count_view if model.stats else 0,
        )

    def _to_model(self, entity: Cheatsheet) -> CheatsheetModel:
        model = CheatsheetModel(
            cheatsheet_id=entity.cheatsheet_id,
            title=entity.title,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_public=entity.is_public,
            stats=StatsModel(
                count_like=entity.count_like,
                count_view=entity.count_view,
                cheatsheet_id=entity.cheatsheet_id,
            ),
        )

        if hasattr(entity, "tags") and entity.tags:
            model.tags_association = [
                CheatsheetToTagModel(
                    cheatsheet_id=entity.cheatsheet_id,
                    tag_id=tag.tag_id,
                    tag=TagModel(tag_id=tag.tag_id, tag_name=tag.tag_name),
                )
                for tag in entity.tags
            ]
        return model

    async def get_by_id(self, cheatsheet_id: int) -> Cheatsheet | None:
        statement = (
            select(CheatsheetModel)
            .where(CheatsheetModel.cheatsheet_id == cheatsheet_id)
            .options(
                joinedload(CheatsheetModel.stats),
                selectinload(CheatsheetModel.tags_association).joinedload(
                    CheatsheetToTagModel.tag
                ),
            )
        )
        result = await self._session.execute(statement)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        model = self._to_model(cheatsheet)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(
            model, ["stats", "tags_association", "tags_association.tag"]
        )
        return self._to_entity(model)
