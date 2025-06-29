from abc import ABC, abstractmethod

from application.dto.schemas import CheatsheetRead, TagRead
from infrastructure.repositories.cheatsheet_repository import (
    SQLAlchemyCheatsheetRepository,
)


class ICheatsheetUseCase(ABC):

    @abstractmethod
    async def get_cheatsheet_by_id(
        self, cheatsheet_id: int
    ) -> CheatsheetRead | None:
        pass


class CheatsheetUseCase(ICheatsheetUseCase):
    def __init__(
        self,
        repo: SQLAlchemyCheatsheetRepository,
    ):
        self._repo = repo

    async def get_cheatsheet_by_id(
        self, cheatsheet_id: int
    ) -> CheatsheetRead | None:
        cheatsheet = await self._repo.get_by_id(cheatsheet_id)
        if not cheatsheet:
            return None

        return CheatsheetRead(
            cheatsheet_id=cheatsheet.cheatsheet_id,
            title=cheatsheet.title,
            content=cheatsheet.content,
            created_at=cheatsheet.created_at,
            updated_at=cheatsheet.updated_at,
            is_public=cheatsheet.is_public,
            tags=[
                TagRead(tag_id=tag.tag_id, tag_name=tag.tag_name)
                for tag in cheatsheet.tags
            ],
            count_like=cheatsheet.count_like,
            count_view=cheatsheet.count_view,
        )
