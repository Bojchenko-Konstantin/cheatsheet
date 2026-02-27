from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.application.dto import User
from src.application.interfaces import IUnitOfWork
from src.application.use_cases import CheatsheetUseCase
from src.application.use_cases.jwt import JWTUseCase
from src.application.use_cases.user import UserUseCase
from src.core.config import settings
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


async def get_unit_of_work() -> SQLAlchemyUnitOfWork:
    async with SQLAlchemyUnitOfWork() as unit_of_work:
        return unit_of_work


def get_user_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> UserUseCase:
    return UserUseCase(unit_of_work=unit_of_work)


def get_jwt_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> JWTUseCase:
    return JWTUseCase(
        unit_of_work=unit_of_work,
        private_key=settings.jwt.private_key,
        public_key=settings.jwt.public_key,
        algorithm=settings.jwt.algorithm,
        access_token_expires_in=settings.jwt.access_token_expires_in,
        refresh_token_expires_in=settings.jwt.refresh_token_expires_in,
    )


def get_cheatsheet_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(unit_of_work=unit_of_work)


async def get_current_user_required(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
) -> User:
    """
    Mandatory dependency for retrieving the current authenticated user.

    Used in endpoints that require authentication.
    Raises HTTPException 401 if token is missing, invalid, or user not found.
    """
    payload = await jwt_use_case.verify_access_token(access_token)
    user = await user_use_case.get_by_id(payload.user_id)
    return user


async def get_current_user_optional(
    access_token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
) -> User | None:
    """
    Retrieves current user from JWT token if provided and valid.

    Unlike get_current_user_required, this dependency does not raise an exception
    when the token is missing or invalid, but returns None instead.
    """
    if not access_token:
        return None

    try:
        payload = await jwt_use_case.verify_access_token(access_token)
        user = await user_use_case.get_by_id(payload.user_id)
        return user
    except Exception:
        return None


# Type aliases for dependencies
OAuth2FormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
OAuth2SchemeRequiredDep = Annotated[str, Depends(oauth2_scheme)]
OAuth2SchemeOptionalDep = Annotated[str | None, Depends(oauth2_scheme_optional)]

UserUseCaseDep = Annotated[UserUseCase, Depends(get_user_use_case)]
JWTUseCaseDep = Annotated[JWTUseCase, Depends(get_jwt_use_case)]
CheatsheetUseCaseDep = Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)]

CurrentUserRequiredDep = Annotated[User, Depends(get_current_user_required)]
CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]
