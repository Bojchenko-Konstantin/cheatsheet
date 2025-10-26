from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Bundle
from sqlalchemy.sql.selectable import Select


class DictBundle(Bundle):
    def create_row_processor(
        self,
        query: Select[Any],
        procs: Sequence[Callable[[Row[Any]], Any]],
        labels: Sequence[str],
    ) -> Callable[[Row[Any]], Any]:
        """
        Override create_row_processor to return values as dictionaries.
        """

        def proc(row: Row[Any]) -> dict[str, Any]:
            return dict(zip(labels, (proc(row) for proc in procs), strict=True))

        return proc
