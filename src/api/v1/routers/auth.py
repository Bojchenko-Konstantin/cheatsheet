import logging

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    JWTUseCaseDep,
    OAuth2FormDep,
    UserUseCaseDep,
)
from src.api.schemas import TokenPair, TokenVerification, UserCreate
from src.application.dto import UserPayload
from src.application.exceptions import (
    AccessTokenException,
    AccessTokenExpiredError,
    DuplicateUserError,
    RefreshTokenNotFoundError,
    UserAuthenticationError,
    UserCreationError,
    UserInactiveError,
    UserNotFoundError,
)

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenPair)
async def login(
    user_form: OAuth2FormDep,
    user_use_case: UserUseCaseDep,
    jwt_use_case: JWTUseCaseDep,
):
    try:
        user = await user_use_case.authenticate_user(
            user_form.username, user_form.password
        )
    except UserNotFoundError as e:
        logger.debug("User with username %s was not found", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authorize",
        ) from e
    except UserAuthenticationError as e:
        logger.exception("Failed login attempt for username: %s", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid username or password",
        ) from e
    except UserInactiveError as e:
        logger.warning("Inactive user attempted login: %s", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Account is inactive",
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

    payload = UserPayload.create(user_id=user.user_id, is_superuser=user.is_superuser)

    try:
        token_pair = await jwt_use_case.get_jwt_tokens(payload)
    except AccessTokenExpiredError as e:
        logger.exception("Access token expired: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from e
    except AccessTokenException as e:
        logger.exception(
            "Failed to generate access token for username: %s", user_form.username
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authorize. Please try again later.",
        ) from e

    return token_pair


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(
    user_form: UserCreate,
    user_use_case: UserUseCaseDep,
    jwt_use_case: JWTUseCaseDep,
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

    try:
        token_pair = await jwt_use_case.get_jwt_tokens(payload)
    except AccessTokenExpiredError as e:
        logger.exception("Access token expired: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from e
    except AccessTokenException as e:
        logger.exception(
            "Failed to generate access token for username: %s", user_form.username
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authorize. Please try again later.",
        ) from e

    return token_pair


@router.post("/refresh")
async def refresh(
    token_verification: TokenVerification,
    user_use_case: UserUseCaseDep,
    jwt_use_case: JWTUseCaseDep,
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

    try:
        token_pair = await jwt_use_case.get_jwt_tokens(payload)
    except AccessTokenExpiredError as e:
        logger.exception("Access token expired: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from e
    except AccessTokenException as e:
        logger.exception(
            "Failed to generate access token for user with id: %s",
            token_verification.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authorize. Please try again later.",
        ) from e

    return token_pair
