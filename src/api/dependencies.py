from fastapi import Depends

from src.application.interfaces import IUnitOfWork
from src.application.use_cases import CheatsheetUseCase
from src.application.use_cases.jwt import JWTUseCase
from src.application.use_cases.user import UserUseCase
from src.core.config import settings
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def get_unit_of_work() -> SQLAlchemyUnitOfWork:
    async with SQLAlchemyUnitOfWork() as unit_of_work:
        return unit_of_work


async def get_cheatsheet_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(unit_of_work=unit_of_work)


async def get_user_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> UserUseCase:
    return UserUseCase(unit_of_work=unit_of_work)


def get_jwt_use_case() -> JWTUseCase:
    return JWTUseCase(
        private_key=settings.jwt.private_key,
        public_key=settings.jwt.public_key,
        algorithm=settings.jwt.algorithm,
        access_token_expires_in=settings.jwt.access_token_expires_in,
        refresh_token_expires_in=settings.jwt.refresh_token_expires_in,
    )
