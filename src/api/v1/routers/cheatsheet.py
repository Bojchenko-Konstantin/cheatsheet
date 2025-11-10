import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_cheatsheet_use_case
from src.api.schemas import CheatsheetCreate, CheatsheetRead, CheatsheetUpdate
from src.application.exceptions import (
    CheatsheetCreationError,
    CheatsheetNotFoundError,
    CheatsheetUpdateError,
)
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
        logger.exception("Cheatsheet with id %s was not found", cheatsheet_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cheatsheet with id {cheatsheet_id} was not found",
        ) from e

    logger.debug("Cheatsheet with id %s: %s", cheatsheet_id, cheatsheet)
    return cheatsheet


@router.post("/", response_model=CheatsheetRead, status_code=status.HTTP_201_CREATED)
async def create_cheatsheet(
    cheatsheet_data: CheatsheetCreate,
    cheatsheet_use_case: Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)],
):
    cheatsheet_to_create = Cheatsheet.from_dict(cheatsheet_data.model_dump())

    try:
        cheatsheet = await cheatsheet_use_case.create(cheatsheet_to_create)
    except CheatsheetCreationError as e:
        logger.exception(
            "Cheatsheet with data %s failed to be created", cheatsheet_data
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cheatsheet was not created",
        ) from e

    logger.debug("Cheatsheet with id %s: %s", cheatsheet.cheatsheet_id, cheatsheet)
    return cheatsheet


@router.put("/{cheatsheet_id}", response_model=CheatsheetRead)
async def update_cheatsheet(
    cheatsheet_id: UUID,
    cheatsheet_data: CheatsheetUpdate,
    cheatsheet_use_case: Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)],
):
    try:
        update_data: dict[str, Any] = cheatsheet_data.model_dump(exclude_unset=True)
        cheatsheet_with_updated_data = Cheatsheet.from_dict(
            dict(cheatsheet_id=cheatsheet_id, **update_data)
        )

        updated_cheatsheet = await cheatsheet_use_case.update(
            cheatsheet_with_updated_data=cheatsheet_with_updated_data,
        )

    except CheatsheetUpdateError as e:
        logger.exception(
            "Cheatsheet %s failed to be updated with data: %s",
            cheatsheet_id,
            cheatsheet_data,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cheatsheet was not updated",
        ) from e

    logger.debug("Cheatsheet: %s", updated_cheatsheet)
    return updated_cheatsheet
