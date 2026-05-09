from __future__ import annotations

import contextlib
from datetime import datetime
from typing import Self
from uuid import UUID

from sqlalchemy import JSON, func, or_, select, text
from sqlalchemy.sql import Select

from src.application.interfaces.services import CursorDTO
from src.infrastructure.database.models import (
    CheatsheetModel,
    CheatsheetStatsModel,
    TagModel,
)
from src.infrastructure.repositories.utils import DictBundle


class CheatsheetQueryBuilder:
    """Builder for constructing SQL queries for cheatsheet listing."""

    _SIMILARITY_THRESHOLD_SEARCH: float = 0.2

    def __init__(self) -> None:
        self._query: Select = self._build_base_query()

    def _build_base_query(self) -> Select:
        return (
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
                func.coalesce(
                    func.json_agg(
                        func.json_build_object(
                            "tag_id",
                            TagModel.tag_id,
                            "tag_name",
                            TagModel.tag_name,
                        )
                    ).filter(TagModel.tag_id.isnot(None)),
                    func.cast(text("'[]'"), JSON),
                ).label("tags"),
            )
            .join(CheatsheetModel.stats)
            .outerjoin(CheatsheetModel.tags)
            .group_by(
                CheatsheetModel.cheatsheet_id,
                CheatsheetStatsModel.count_like,
                CheatsheetStatsModel.count_view,
            )
        )

    def apply_access_filter(self, user_id: UUID | None) -> Self:
        """Filter cheatsheets based on user access rights."""
        if user_id:
            self._query = self._query.where(
                or_(
                    CheatsheetModel.is_public,
                    CheatsheetModel.user_id == user_id,
                )
            )
        else:
            self._query = self._query.where(CheatsheetModel.is_public)
        return self

    def apply_tag_filter(self, tag: str | None) -> Self:
        """Filter cheatsheets by exact tag name match."""
        if tag:
            self._query = self._query.where(TagModel.tag_name == tag)
        return self

    def apply_search(self, search: str | None) -> Self:
        """Apply search conditions."""
        if search:
            self._query = self._query.where(
                or_(
                    CheatsheetModel.title.ilike(f"%{search}%"),
                    CheatsheetModel.content.ilike(f"%{search}%"),
                    func.similarity(CheatsheetModel.title, search)
                    > self._SIMILARITY_THRESHOLD_SEARCH,
                )
            )
        return self

    def apply_sorting(
        self,
        sort_by: str,
        sort_order: str,
        search: str | None = None,
    ) -> Self:
        """Apply ordering to the query."""
        if search:
            self._query = self._query.order_by(
                func.greatest(
                    func.similarity(CheatsheetModel.title, search),
                    func.similarity(CheatsheetModel.content, search),
                ).desc()
            )
        else:
            sort_column = getattr(CheatsheetModel, sort_by)
            if sort_order == "desc":
                self._query = self._query.order_by(
                    sort_column.desc(),
                    CheatsheetModel.cheatsheet_id.desc(),
                )
            else:
                self._query = self._query.order_by(
                    sort_column.asc(),
                    CheatsheetModel.cheatsheet_id.asc(),
                )
        return self

    def apply_cursor(
        self,
        cursor: CursorDTO | None,
        sort_by: str,
        sort_order: str,
    ) -> Self:
        """Apply cursor-based pagination filter."""
        if cursor is None:
            return self

        sort_column = getattr(CheatsheetModel, sort_by)
        cursor_sort_value = cursor.sort_value

        with contextlib.suppress(ValueError, TypeError):
            if not isinstance(cursor_sort_value, datetime):
                cursor_sort_value = datetime.fromtimestamp(int(cursor_sort_value))

        if sort_order == "desc":
            self._query = self._query.where(
                or_(
                    sort_column < cursor_sort_value,
                    (sort_column == cursor_sort_value)
                    & (CheatsheetModel.cheatsheet_id < cursor.entity_id),
                )
            )
        else:
            self._query = self._query.where(
                or_(
                    sort_column > cursor_sort_value,
                    (sort_column == cursor_sort_value)
                    & (CheatsheetModel.cheatsheet_id > cursor.entity_id),
                )
            )
        return self

    def apply_suggestions_titles(
        self,
        query: str,
        limit: int,
        threshold: float,
    ) -> Select:
        """Build query for title suggestions."""
        return (
            select(CheatsheetModel.title)
            .where(
                or_(
                    CheatsheetModel.title.ilike(f"%{query}%"),
                    func.similarity(CheatsheetModel.title, query) > threshold,
                )
            )
            .order_by(func.similarity(CheatsheetModel.title, query).desc())
            .limit(limit)
        )

    def apply_suggestions_tags(
        self,
        query: str,
        limit: int,
        threshold: float,
    ) -> Select:
        """Build query for tag suggestions."""
        return (
            select(TagModel.tag_name)
            .where(
                or_(
                    TagModel.tag_name.ilike(f"%{query}%"),
                    func.similarity(TagModel.tag_name, query) > threshold,
                )
            )
            .order_by(func.similarity(TagModel.tag_name, query).desc())
            .limit(limit)
        )

    def build(self) -> Select:
        return self._query
