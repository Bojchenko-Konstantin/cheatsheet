from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import (
    CheatsheetCreationError,
    CheatsheetNotFoundError,
    CheatsheetUpdateError,
)
from src.application.interfaces import ICheatsheetRepo
from src.domain.entities import Cheatsheet
from src.infrastructure.database.models import (
    CheatsheetModel,
    CheatsheetStatsModel,
    CheatsheetToTagModel,
    TagModel,
)
from src.infrastructure.repositories.utils import DictBundle


class SQLAlchemyCheatsheetRepo(ICheatsheetRepo):
    """
    Class for operations with cheatsheets that interact with database using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_model(self, entity: Cheatsheet) -> CheatsheetModel:
        kwargs = entity.to_dict()
        tags = kwargs.pop("tags")
        cheatsheet_id = kwargs["cheatsheet_id"]
        count_like = kwargs.pop("count_like")
        count_view = kwargs.pop("count_view")

        model = CheatsheetModel(**kwargs)

        for tag in tags:
            model.tag_associations.append(
                CheatsheetToTagModel(cheatsheet_id=cheatsheet_id, tag_id=tag.tag_id)
            )

        model.stats = CheatsheetStatsModel(count_like=count_like, count_view=count_view)

        return model

    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        statement = (
            select(
                DictBundle(
                    "cheatsheet",
                    CheatsheetModel.cheatsheet_id,
                    CheatsheetModel.title,
                    CheatsheetModel.content,
                    CheatsheetModel.created_at,
                    CheatsheetModel.updated_at,
                    CheatsheetModel.is_public,
                    CheatsheetStatsModel.count_view,
                    CheatsheetStatsModel.count_like,
                ),
                func.json_agg(
                    func.json_build_object(
                        "tag_id", TagModel.tag_id, "tag_name", TagModel.tag_name
                    )
                ).label("tags"),
            )
            .join(CheatsheetModel.stats)
            .join(CheatsheetModel.tags)
            .where(CheatsheetModel.cheatsheet_id == cheatsheet_id)
            .group_by(CheatsheetModel.cheatsheet_id, CheatsheetStatsModel.cheatsheet_id)
        )
        result = await self._session.execute(statement)
        model = result.one_or_none()

        if not model:
            raise CheatsheetNotFoundError

        cheatsheet = Cheatsheet.from_dict(dict(**model.cheatsheet, tags=model.tags))
        return cheatsheet

    async def create(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        model = self._to_model(cheatsheet)

        try:
            self._session.add(model)
            await self._session.flush()
        except Exception as e:
            raise CheatsheetCreationError from e

        updated_data = dict(
            cheatsheet_id=model.cheatsheet_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

        updated_cheatsheet = cheatsheet.update(updated_data)
        return updated_cheatsheet

    async def update(self, cheatsheet: Cheatsheet) -> Cheatsheet:
        new_tag_ids = {tag.tag_id for tag in cheatsheet.tags}

        update_statement = (
            update(CheatsheetModel)
            .where(
                CheatsheetModel.cheatsheet_id == cheatsheet.cheatsheet_id,
                select(func.count(TagModel.tag_id))
                .where(TagModel.tag_id.in_(new_tag_ids))
                .scalar_subquery()
                == len(new_tag_ids),
            )
            .values(
                title=cheatsheet.title,
                content=cheatsheet.content,
                is_public=cheatsheet.is_public,
            )
            .returning(CheatsheetModel.cheatsheet_id)
        )

        await self._session.execute(update_statement)

        delete_statement = delete(CheatsheetToTagModel).where(
            CheatsheetToTagModel.cheatsheet_id == cheatsheet.cheatsheet_id
        )
        await self._session.execute(delete_statement)

        if new_tag_ids:
            associations = [
                {"cheatsheet_id": cheatsheet.cheatsheet_id, "tag_id": tag_id}
                for tag_id in new_tag_ids
            ]
            insert_statement = insert(CheatsheetToTagModel).values(associations)
            await self._session.execute(insert_statement)
        try:
            await self._session.flush()

        except Exception as e:
            raise CheatsheetUpdateError from e

        updated_cheatsheet = await self.get_by_id(cheatsheet.cheatsheet_id)
        return updated_cheatsheet
