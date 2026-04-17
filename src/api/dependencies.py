from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.application.dto import User
from src.application.interfaces import IUnitOfWork
from src.application.interfaces.notification_service import INotificationService
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.user_service import IUserService
from src.application.use_cases import CheatsheetUseCase, NotificationUseCase
from src.application.use_cases.auth import AuthUseCase
from src.core.config import settings
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.notification_service import NotiSendNotificationService
from src.infrastructure.token_service import TokenService
from src.infrastructure.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


async def get_unit_of_work() -> SQLAlchemyUnitOfWork:
    async with SQLAlchemyUnitOfWork() as unit_of_work:
        return unit_of_work


def get_cheatsheet_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(unit_of_work=unit_of_work)


def get_token_service() -> TokenService:
    return TokenService(
        private_key=settings.jwt.private_key,
        public_key=settings.jwt.public_key,
        algorithm=settings.jwt.algorithm,
        access_token_expires_in=settings.jwt.access_token_expires_in,
        refresh_token_expires_in=settings.jwt.refresh_token_expires_in,
    )


def get_user_service() -> UserService:
    return UserService()


def get_notification_service() -> INotificationService:
    return NotiSendNotificationService()


def get_notification_use_case(
    notification_service: INotificationService = Depends(get_notification_service),
) -> NotificationUseCase:
    return NotificationUseCase(notification_service=notification_service)


def get_auth_use_case(
    token_service: ITokenService = Depends(get_token_service),
    user_service: IUserService = Depends(get_user_service),
    notification_use_case: NotificationUseCase = Depends(get_notification_use_case),
) -> AuthUseCase:
    return AuthUseCase(token_service, user_service, notification_use_case)


async def get_current_user_required(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    auth_use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> User:
    """
    Mandatory dependency for retrieving the current authenticated user.

    Used in endpoints that require authentication.
    Raises HTTPException 401 if token is missing, invalid, or user not found.
    """
    user = await auth_use_case.get_current_user(access_token)
    return user


async def get_current_user_optional(
    access_token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    auth_use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> User | None:
    """
    Retrieves current user from JWT token if provided and valid.

    Unlike get_current_user_required, this dependency does not raise an exception
    when the token is missing or invalid, but returns None instead.
    """
    if not access_token:
        return None

    try:
        user = await auth_use_case.get_current_user(access_token)
        return user
    except Exception:
        return None


# Type aliases for dependencies.
OAuth2FormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
OAuth2SchemeRequiredDep = Annotated[str, Depends(oauth2_scheme)]
OAuth2SchemeOptionalDep = Annotated[str | None, Depends(oauth2_scheme_optional)]

CheatsheetUseCaseDep = Annotated[CheatsheetUseCase, Depends(get_cheatsheet_use_case)]
AuthUseCaseDep = Annotated[AuthUseCase, Depends(get_auth_use_case)]
NotificationUseCaseDep = Annotated[
    NotificationUseCase, Depends(get_notification_use_case)
]

CurrentUserRequiredDep = Annotated[User, Depends(get_current_user_required)]
CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]
