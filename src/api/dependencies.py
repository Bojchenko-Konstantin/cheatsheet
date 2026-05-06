from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.application.dto import User
from src.application.interfaces import (
    IPasswordResetService,
    ITokenService,
    IUnitOfWork,
    IUserService,
    IVerificationService,
)
from src.application.use_cases import CheatsheetUseCase
from src.application.use_cases.auth import AuthUseCase
from src.application.use_cases.password import PasswordUseCase
from src.application.use_cases.verification import VerificationUseCase
from src.core.config import settings
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.services import (
    EmailVerificationService,
    JWTCoreService,
    PasswordResetService,
    TokenService,
    UserService,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


async def get_unit_of_work() -> SQLAlchemyUnitOfWork:
    async with SQLAlchemyUnitOfWork() as unit_of_work:
        return unit_of_work


def get_cheatsheet_use_case(
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CheatsheetUseCase:
    return CheatsheetUseCase(unit_of_work=unit_of_work)


def get_jwt_core_service() -> JWTCoreService:
    return JWTCoreService(
        private_key=settings.jwt.private_key,
        public_key=settings.jwt.public_key,
        algorithm=settings.jwt.algorithm,
    )


def get_token_service(
    jwt_core: JWTCoreService = Depends(get_jwt_core_service),
) -> TokenService:
    return TokenService(
        jwt_core=jwt_core,
        access_token_expires_in=settings.jwt.access_token_expires_in,
        refresh_token_expires_in=settings.jwt.refresh_token_expires_in,
    )


def get_user_service() -> UserService:
    return UserService()


def get_password_reset_service(
    jwt_core: JWTCoreService = Depends(get_jwt_core_service),
) -> IPasswordResetService:
    return PasswordResetService(
        jwt_core=jwt_core,
        token_expires_in_minutes=settings.password_reset.token_expires_in_minutes,
        frontend_reset_url=settings.password_reset.frontend_url,
    )


def get_email_verification_service(
    jwt_core: JWTCoreService = Depends(get_jwt_core_service),
) -> IVerificationService:
    return EmailVerificationService(
        jwt_core=jwt_core,
        token_expires_in_hours=settings.email_verification.token_expires_in_hours,
        frontend_verify_url=settings.email_verification.frontend_url,
    )


def get_auth_use_case(
    token_service: ITokenService = Depends(get_token_service),
    user_service: IUserService = Depends(get_user_service),
) -> AuthUseCase:
    return AuthUseCase(
        token_service=token_service,
        user_service=user_service,
    )


def get_password_use_case(
    user_service: IUserService = Depends(get_user_service),
    password_reset_service: IPasswordResetService = Depends(get_password_reset_service),
    token_service: ITokenService = Depends(get_token_service),
) -> PasswordUseCase:
    return PasswordUseCase(
        user_service=user_service,
        password_reset_service=password_reset_service,
        token_service=token_service,
    )


def get_verification_use_case(
    user_service: IUserService = Depends(get_user_service),
    email_verification_service: IVerificationService = Depends(
        get_email_verification_service
    ),
) -> VerificationUseCase:
    return VerificationUseCase(
        user_service=user_service,
        email_verification_service=email_verification_service,
    )


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


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_user_required)],
) -> User:
    """Dependency for endpoints that require verified email."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. "
            "Please verify your email to access this feature.",
        )
    return current_user


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
PasswordUseCaseDep = Annotated[PasswordUseCase, Depends(get_password_use_case)]
VerificationUseCaseDep = Annotated[
    VerificationUseCase, Depends(get_verification_use_case)
]


CurrentUserRequiredDep = Annotated[User, Depends(get_current_user_required)]
CurrentVerifiedUserDep = Annotated[User, Depends(get_current_verified_user)]
CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]
