import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_cheatsheet_use_case
from src.api.schemas import CheatsheetCreate, CheatsheetRead
from src.application.exceptions import CheatsheetCreationError, CheatsheetNotFoundError
from src.application.use_cases import CheatsheetUseCase
from src.domain.entities import Cheatsheet

router = APIRouter(prefix="/cheatsheets", tags=["Cheatsheets"])

logger = logging.getLogger(__name__)


@router.get("/{cheatsheet_id}", response_model=CheatsheetRead)
async def get_cheatsheet_by_id(
    cheatsheet_id: UUID,
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


@router.post("/create", response_model=CheatsheetRead)
async def create(
    cheatsheet_data: CheatsheetCreate,
    cheatsheet_use_case: Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)],
):
    cheatsheet_to_create = Cheatsheet.from_dict(cheatsheet_data.model_dump())
    try:
        cheatsheet = await cheatsheet_use_case.create(cheatsheet_to_create)
    except CheatsheetCreationError as e:
        logger.error("Cheatsheet with data %s failed to be created", cheatsheet_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cheatsheet was not created",
        ) from e
    logger.debug("Cheatsheet with id %s: %s", cheatsheet.cheatsheet_id, cheatsheet)
    return cheatsheet
