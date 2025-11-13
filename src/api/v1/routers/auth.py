import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.dependencies import get_jwt_use_case, get_user_use_case
from src.application.use_cases.jwt import JWTUseCase
from src.application.use_cases.user import UserUseCase

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)


@router.post("/login")
async def login(
    user_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
):
    user = await user_use_case.get_by_user_name(user_form.username)

    hashed_password = user.hashed_password
    plain_password = user_form.password

    if (
        user_use_case.verify_password(plain_password, hashed_password)
        and user.is_active
    ):
        payload = dict(user_id=str(user.user_id), is_superuser=user.is_superuser)
        token_pair = await jwt_use_case.get_jwt_tokens(payload)
        return token_pair

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authorize",
        )


@router.post("/register")
async def register():
    pass


@router.post("/token")
def verify_access_token(access_token: str):
    pass


@router.post("/refresh")
async def refresh():
    pass
