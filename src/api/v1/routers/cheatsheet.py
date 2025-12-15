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
    create_data: dict[str, Any] = cheatsheet_data.model_dump(exclude_unset=True)
    # TODO: IMPLEMENT get_current_user! Application won't work without this!
    # Example: create_data["user_id"] = current_user.id

    try:
        cheatsheet = await cheatsheet_use_case.create(create_data)
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
        update_data["cheatsheet_id"] = cheatsheet_id
        # TODO: IMPLEMENT get_current_user! Application won't work without this!
        # Example: update_data["user_id"] = current_user.id

        updated_cheatsheet = await cheatsheet_use_case.update(update_data=update_data)

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
