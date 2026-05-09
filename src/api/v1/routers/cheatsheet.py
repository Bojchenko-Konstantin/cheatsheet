import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    CheatsheetFiltersDep,
    CheatsheetUseCaseDep,
    CurrentUserOptionalDep,
    CurrentVerifiedUserDep,
    CursorPaginationDep,
    SearchSuggestionsDep,
)
from src.api.schemas import (
    CheatsheetCreate,
    CheatsheetListRead,
    CheatsheetRead,
    CheatsheetUpdate,
    SearchSuggestionsRead,
)
from src.application.exceptions import (
    CheatsheetCreationError,
    CheatsheetListError,
    CheatsheetNotFoundError,
    CheatsheetSuggestionsError,
    CheatsheetUpdateError,
    InvalidCursorError,
    InvalidSearchQueryError,
    InvalidSortFieldError,
    InvalidSortOrderError,
)
from src.domain.exceptions import CheatsheetAccessDeniedError

router = APIRouter(prefix="/cheatsheets", tags=["Cheatsheets"])

logger = logging.getLogger(__name__)


@router.get("/", response_model=CheatsheetListRead)
async def get_cheatsheet_list(
    pagination: CursorPaginationDep,
    filters: CheatsheetFiltersDep,
    cheatsheet_use_case: CheatsheetUseCaseDep,
    current_user: CurrentUserOptionalDep,
):
    user_id = current_user.user_id if current_user else None

    try:
        cheatsheet_list = await cheatsheet_use_case.get_cheatsheet_list(
            user_id=user_id,
            cursor=pagination.cursor,
            size=pagination.size,
            tag=filters.tag,
            search=filters.search,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )
    except InvalidCursorError as e:
        logger.warning(
            "Invalid cursor parameter: cursor=%s, size=%s, user_id=%s",
            pagination.cursor,
            pagination.size,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cursor parameter.",
        ) from e
    except InvalidSearchQueryError as e:
        logger.warning(
            "Invalid search query: search=%s, user_id=%s",
            filters.search,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except (InvalidSortFieldError, InvalidSortOrderError) as e:
        logger.warning(
            "Invalid sort parameters: sort_by=%s, sort_order=%s, user_id=%s",
            filters.sort_by,
            filters.sort_order,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except CheatsheetListError as e:
        logger.exception(
            "Failed to get cheatsheet list: cursor=%s, size=%s, tag=%s, "
            "search=%s, sort_by=%s, sort_order=%s, user_id=%s",
            pagination.cursor,
            pagination.size,
            filters.tag,
            filters.search,
            filters.sort_by,
            filters.sort_order,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cheatsheets due to an internal error.",
        ) from e
    except Exception as e:
        logger.exception(
            "Unexpected error retrieving cheatsheet list for user_id: %s",
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving cheatsheets.",
        ) from e

    return cheatsheet_list


@router.get("/suggestions", response_model=SearchSuggestionsRead)
async def get_search_suggestions(
    params: SearchSuggestionsDep,
    cheatsheet_use_case: CheatsheetUseCaseDep,
):
    try:
        suggestions = await cheatsheet_use_case.get_search_suggestions(
            query=params.query,
            limit=params.limit,
        )
    except InvalidSearchQueryError as e:
        logger.warning(
            "Invalid suggestions request: query=%s, limit=%s",
            params.query,
            params.limit,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except CheatsheetSuggestionsError as e:
        logger.exception(
            "Failed to get search suggestions: query=%s, limit=%s",
            params.query,
            params.limit,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search suggestions due to an internal error.",
        ) from e
    except Exception as e:
        logger.exception(
            "Unexpected error retrieving suggestions: %s",
            params.query,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving suggestions.",
        ) from e

    return suggestions


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
    current_user: CurrentVerifiedUserDep,
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
    current_user: CurrentVerifiedUserDep,
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
