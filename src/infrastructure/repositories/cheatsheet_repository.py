from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.application.interfaces import ICheatsheetRepo
from src.domain.entities import Cheatsheet, Tag
from src.infrastructure.database.models import (
    CheatsheetModel,
    CheatsheetToTagModel,
    TagModel,
)


class SQLAlchemyCheatsheetRepo(ICheatsheetRepo):
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
                    tag_id=tag_association.tag.tag_id,
                    tag_name=tag_association.tag.tag_name,
                )
                for tag_association in model.tags_association
            ],
            count_like=model.stats.count_like,
            count_view=model.stats.count_view,
        )

    def _to_model(self, entity: Cheatsheet) -> CheatsheetModel:
        model = CheatsheetModel(**asdict(entity))

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
        await self._session.refresh(
            model, ["stats", "tags_association", "tags_association.tag"]
        )
        return self._to_entity(model)
