import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_cheatsheet_use_case
from src.api.schemas import CheatsheetRead
from src.application.exceptions import CheatsheetNotFoundError
from src.application.use_cases import CheatsheetUseCase

router = APIRouter(prefix="/cheatsheets", tags=["Cheatsheets"])

logger = logging.getLogger(__name__)


@router.get("/{cheatsheet_id}", response_model=CheatsheetRead)
async def get_cheatsheet_by_id(
    cheatsheet_id: uuid.UUID,
    cheatsheet_use_case: Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)],
):
    try:
        cheatsheet = await cheatsheet_use_case.get_by_id(cheatsheet_id)
    except CheatsheetNotFoundError as e:
        logger.debug("Cheatsheet with id %s was not found", cheatsheet_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cheatsheet with id {cheatsheet_id} was not found",
        ) from e
    logger.debug("Cheatsheet with id %s: %s", cheatsheet_id, cheatsheet)
    return cheatsheet
