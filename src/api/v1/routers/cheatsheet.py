import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import get_cheatsheet_use_case
from src.application.dto.schemas import CheatsheetRead
from src.application.use_cases import CheatsheetUseCase

router = APIRouter(prefix="/cheatsheets", tags=["Cheatsheets"])

logger = logging.getLogger(__name__)


@router.get("/{cheatsheet_id}")
async def get_cheatsheet_by_id(
    cheatsheet_id: int,
    cheatsheet_use_case: Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)],
) -> CheatsheetRead:
    cheatsheet = await cheatsheet_use_case.get_by_id(cheatsheet_id)
    if not cheatsheet:
        logger.debug("Cheatsheet with id %s was not found", cheatsheet_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cheatsheet was not found",
        )
    logger.debug("Cheatsheet with id %s: %s", cheatsheet_id, cheatsheet)
    return cheatsheet
