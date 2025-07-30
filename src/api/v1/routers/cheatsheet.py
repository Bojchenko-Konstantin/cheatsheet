from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.dependencies import get_cheatsheet_use_case
from application.dto.schemas import CheatsheetRead
from application.use_cases.cheatsheet import CheatsheetUseCase

router = APIRouter(prefix="/cheatsheets", tags=["Cheatsheets"])


@router.get("/{cheatsheet_id}", response_model=CheatsheetRead)
async def get_cheatsheet_by_id(
    cheatsheet_id: int,
    use_case: CheatsheetUseCase = Depends(get_cheatsheet_use_case),
):
    cheatsheet = await use_case.get_cheatsheet_by_id(cheatsheet_id)
    if not cheatsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шпаргалка не найдена",
        )
    return cheatsheet
