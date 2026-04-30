import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    CheatsheetUseCaseDep,
    CurrentUserOptionalDep,
    CurrentUserRequiredDep,
)
from src.api.schemas import CheatsheetCreate, CheatsheetRead, CheatsheetUpdate
from src.application.exceptions import (
    CheatsheetCreationError,
    CheatsheetNotFoundError,
    CheatsheetUpdateError,
)
from src.domain.exceptions import CheatsheetAccessDeniedError

router = APIRouter(prefix="/cheatsheets", tags=["Cheatsheets"])

logger = logging.getLogger(__name__)


@router.get("/{cheatsheet_id}", response_model=CheatsheetRead)
async def get_cheatsheet_by_id(
    cheatsheet_id: UUID,
    cheatsheet_use_case: CheatsheetUseCaseDep,
    current_user: CurrentUserOptionalDep,
):
    try:
        current_user_id = current_user.user_id if current_user else None
        cheatsheet = await cheatsheet_use_case.get_by_id(cheatsheet_id, current_user_id)
    except CheatsheetAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this cheatsheet",
        ) from e
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
    cheatsheet_use_case: CheatsheetUseCaseDep,
    current_user: CurrentUserRequiredDep,
):
    create_data: dict[str, Any] = cheatsheet_data.model_dump(exclude_unset=True)
    create_data["user_id"] = current_user.user_id

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
    cheatsheet_use_case: CheatsheetUseCaseDep,
    current_user: CurrentUserRequiredDep,
):
    update_data: dict[str, Any] = cheatsheet_data.model_dump(exclude_unset=True)
    update_data["cheatsheet_id"] = cheatsheet_id
    update_data["user_id"] = current_user.user_id

    try:
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
