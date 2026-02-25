import contextlib
from collections.abc import MutableMapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, func, insert, select, update
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


@dataclass(frozen=True, slots=True)
class CheatsheetStats:
    count_like: int = 0
    count_view: int = 0


class SQLAlchemyCheatsheetRepo(ICheatsheetRepo):
    """
    Class for operations with cheatsheets that interact with database using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_model(
        self, cheatsheet: Cheatsheet | MutableMapping[str, Any]
    ) -> CheatsheetModel:
        kwargs = (
            cheatsheet.to_dict()
            if isinstance(cheatsheet, Cheatsheet)
            else deepcopy(cheatsheet)
        )
        tags = kwargs.pop("tags")
        cheatsheet_id = kwargs.get("cheatsheet_id")
        count_like = kwargs.pop("count_like", None)
        count_view = kwargs.pop("count_view", None)

        model = CheatsheetModel(**kwargs)

        for tag in tags:
            model.tag_associations.append(
                CheatsheetToTagModel(
                    cheatsheet_id=cheatsheet_id,
                    tag_id=(
                        tag["tag_id"] if isinstance(tag, MutableMapping) else tag.tag_id
                    ),
                )
            )

        model.stats = CheatsheetStatsModel(count_like=count_like, count_view=count_view)

        return model

    async def get_by_id(self, cheatsheet_id: UUID) -> Cheatsheet:
        statement = (
            select(
                DictBundle(
                    "cheatsheet",
                    CheatsheetModel.cheatsheet_id,
                    CheatsheetModel.user_id,
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

    async def create(self, create_data: dict[str, Any]) -> Cheatsheet:
        model = self._to_model(create_data)

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

        created_cheatsheet = Cheatsheet.from_dict(dict(**create_data, **updated_data))
        return created_cheatsheet

    async def update(self, update_data: dict[str, Any]) -> Cheatsheet:
        stats_statement = select(
            CheatsheetStatsModel.count_like, CheatsheetStatsModel.count_view
        ).where(CheatsheetStatsModel.cheatsheet_id == update_data["cheatsheet_id"])

        current_stats = CheatsheetStats()

        with contextlib.suppress(Exception):
            stats_result = await self._session.execute(stats_statement)
            current_stats = stats_result.one()

        update_statement = (
            update(CheatsheetModel)
            .where(CheatsheetModel.cheatsheet_id == update_data["cheatsheet_id"])
            .values(
                title=update_data["title"],
                content=update_data["content"],
                is_public=update_data["is_public"],
            )
            .returning(
                CheatsheetModel.created_at,
                CheatsheetModel.updated_at,
            )
        )

        try:
            [result] = await self._session.execute(update_statement)
        except Exception as e:
            raise CheatsheetUpdateError(
                f"Failed to update cheatsheet {update_data['cheatsheet_id']}."
            ) from e

        updated_cheatsheet = self._get_new_cheatsheet(
            result, current_stats, update_data
        )
        await self._update_tags(updated_cheatsheet)

        return updated_cheatsheet

    @staticmethod
    def _get_new_cheatsheet(
        result_time: Row[tuple[datetime, datetime]],
        current_stats: Row[tuple[int, int]] | CheatsheetStats,
        update_data: dict[str, Any],
    ) -> Cheatsheet:
        cheatsheet = Cheatsheet.from_dict(
            dict(
                created_at=result_time.created_at,
                updated_at=result_time.updated_at,
                count_like=current_stats.count_like,
                count_view=current_stats.count_view,
                **update_data,
            )
        )
        return cheatsheet

    async def _update_tags(self, cheatsheet: Cheatsheet) -> None:
        await self._delete_old_tags(cheatsheet)

        assert isinstance(cheatsheet.tags, set)

        await self._insert_new_tags(cheatsheet)

    async def _delete_old_tags(self, cheatsheet: Cheatsheet) -> None:
        delete_tags_statement = delete(CheatsheetToTagModel).where(
            CheatsheetToTagModel.cheatsheet_id == cheatsheet.cheatsheet_id
        )

        try:
            await self._session.execute(delete_tags_statement)
        except Exception as e:
            raise CheatsheetUpdateError(
                f"Failed to clear old tags for cheatsheet {cheatsheet.cheatsheet_id}."
            ) from e

    async def _insert_new_tags(self, cheatsheet: Cheatsheet) -> None:
        tag_ids = [tag.tag_id for tag in cheatsheet.tags]
        insert_tags_data = [
            dict(cheatsheet_id=cheatsheet.cheatsheet_id, tag_id=tag_id)
            for tag_id in tag_ids
        ]
        insert_tags_statement = insert(CheatsheetToTagModel).values(insert_tags_data)

        try:
            await self._session.execute(insert_tags_statement)
        except Exception as e:
            raise CheatsheetUpdateError(
                f"Tags insertion failed for cheatsheet {cheatsheet.cheatsheet_id}."
            ) from e
