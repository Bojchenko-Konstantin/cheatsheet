import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.dependencies import (
    get_jwt_use_case,
    get_user_use_case,
    oauth2_scheme,
    oauth2_scheme_optional,
)
from src.api.schemas import TokenPair, TokenVerification, UserCreate
from src.application.dto import User, UserPayload
from src.application.exceptions import (
    AccessTokenException,
    AccessTokenExpiredError,
    AccessTokenGenerationError,
    DuplicateUserError,
    RefreshTokenNotFoundError,
    UserCreationError,
    UserNotFoundError,
)
from src.application.use_cases.jwt import JWTUseCase
from src.application.use_cases.user import UserUseCase

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenPair)
async def login(
    user_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
):
    try:
        user = await user_use_case.get_by_user_name(user_form.username)

    except UserNotFoundError as e:
        logger.debug("User with username %s was not found", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User with username {user_form.username} was not found",
        ) from e

    except Exception as e:
        logger.exception(
            "Unexpected error during login for username: %s",
            user_form.username,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login. Please try again later.",
        ) from e

    hashed_password = user.hashed_password
    plain_password = user_form.password

    if (
        user_use_case.verify_password(plain_password, hashed_password)
        and user.is_active
    ):
        payload = UserPayload.create(
            user_id=user.user_id, is_superuser=user.is_superuser
        )

        try:
            token_pair = await jwt_use_case.get_jwt_tokens(payload)

        except AccessTokenGenerationError as e:
            logger.exception(
                "Failed to generate access token for username: %s", user_form.username
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authorize. Please try again later.",
            ) from e

        return token_pair

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(
    user_form: UserCreate,
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
):
    create_data = user_form.model_dump(exclude_unset=True)

    try:
        user = await user_use_case.create(create_data)

    except DuplicateUserError as e:
        logger.debug(
            "User registration failed - username '%s' already exists.",
            user_form.username,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username '{user_form.username}' already exists. "
            "Please choose another one.",
        ) from e

    except UserCreationError as e:
        logger.exception(
            "Unexpected error during user registration for username: %s",
            user_form.username,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration. "
            "Please try again later.",
        ) from e

    payload = UserPayload.create(user_id=user.user_id, is_superuser=user.is_superuser)
    token_pair = await jwt_use_case.get_jwt_tokens(payload)
    return token_pair


@router.post("/refresh")
async def refresh(
    token_verification: TokenVerification,
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
):
    try:
        await jwt_use_case.verify_refresh_token(
            user_id=token_verification.user_id,
            plain_refresh_token=token_verification.refresh_token,
            fingerprint=token_verification.fingerprint,
        )

    except RefreshTokenNotFoundError as e:
        logger.exception(
            "Refresh token not found for user_id: %s", token_verification.user_id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from e

    try:
        user = await user_use_case.get_by_id(token_verification.user_id)

    except UserNotFoundError as e:
        logger.debug("User with id %s was not found", token_verification.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authorize",
        ) from e

    payload = UserPayload.create(user_id=user.user_id, is_superuser=user.is_superuser)
    token_pair = await jwt_use_case.get_jwt_tokens(payload)
    return token_pair


async def get_current_user_required(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    jwt_use_case: Annotated[JWTUseCase, Depends(get_jwt_use_case)],
    user_use_case: Annotated[UserUseCase, Depends(get_user_use_case)],
):
    """
    Mandatory dependency for retrieving the current authenticated user.

    Used in endpoints that require authentication.
    Raises HTTPException 401 if token is missing, invalid, or user not found.

    Why this approach:
    - Single place to handle authentication errors
    - Guarantees that user exists and is authenticated
    - Reusable across any endpoints that need protection
    """
    try:
        payload = await jwt_use_case.verify_access_token(access_token)

    except AccessTokenExpiredError as e:
        logger.exception(f"Access token expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to authorize"
        ) from e

    except AccessTokenException as e:
        logger.exception(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to authorize"
        ) from e

    except Exception as e:
        logger.critical(
            f"Unexpected error during token verification: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication.",
        ) from e

    try:
        user = await user_use_case.get_by_id(UUID(payload.user_id))

    except UserNotFoundError as e:
        logger.debug("User with id %s was not found", payload.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authorize",
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from e

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

    Why this approach:
    - Avoids boilerplate code duplication across endpoints
    - Endpoint must work without authentication (public access)
    - But if user is authenticated, we can:
        * Check access to private resources
    - Exceptions are intentionally not propagated:
        * Request won't be interrupted due to token issues
        * Client receives public version instead of an error
    """

    if not access_token:
        return None

    try:
        payload = await jwt_use_case.verify_access_token(access_token)
        user = await user_use_case.get_by_id(UUID(payload.user_id))
        return user

    except Exception:
        return None
