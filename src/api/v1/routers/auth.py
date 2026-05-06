import contextlib
import logging

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    AuthUseCaseDep,
    CurrentUserRequiredDep,
    CurrentVerifiedUserDep,
    OAuth2FormDep,
    PasswordUseCaseDep,
    VerificationUseCaseDep,
)
from src.api.schemas import (
    EmailVerificationConfirm,
    EmailVerificationResponse,
    EmailVerificationSendResponse,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordUpdate,
    PasswordUpdateResponse,
    TokenPair,
    TokenVerification,
    UserCreate,
)
from src.application.dto.email import EmailVerificationData, PasswordResetEmailData
from src.application.exceptions import (
    AccessTokenException,
    AccessTokenExpiredError,
    DuplicateUserError,
    EmailAlreadyVerifiedError,
    ExpiredEmailVerificationTokenError,
    ExpiredPasswordResetTokenError,
    InvalidEmailVerificationTokenError,
    InvalidPasswordResetTokenError,
    RefreshTokenCompromisedError,
    RefreshTokenNotFoundError,
    RevokeRefreshTokenError,
    UserAuthenticationError,
    UserCreationError,
    UserInactiveError,
    UserNotFoundError,
)
from src.infrastructure.background_tasks import (
    send_email_verification,
    send_password_changed_email,
    send_password_reset_email,
    send_welcome_email,
)

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenPair)
async def login(
    user_form: OAuth2FormDep,
    auth_use_case: AuthUseCaseDep,
):
    try:
        token_pair = await auth_use_case.authenticate(
            user_form.username, user_form.password
        )
    except UserNotFoundError as e:
        logger.debug("User with username %s was not found", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to authorize",
        ) from e
    except UserAuthenticationError as e:
        logger.debug("Failed login attempt for username: %s", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid username or password",
        ) from e
    except UserInactiveError as e:
        logger.warning("Inactive user attempted login: %s", user_form.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Account is inactive",
        ) from e

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
    auth_use_case: AuthUseCaseDep,
    verification_use_case: VerificationUseCaseDep,
):
    create_data = user_form.model_dump(exclude_unset=True)

    try:
        token_pair = await auth_use_case.register(create_data)

        email = create_data.get("email")
        user_name = create_data.get("username")

        if email:
            with contextlib.suppress(Exception):
                await send_welcome_email.kiq(  # type: ignore[call-overload]
                    email=email,
                    user_name=user_name,
                )
            with contextlib.suppress(Exception):
                user = await auth_use_case.get_current_user(token_pair["access_token"])
                verification_data = (
                    await verification_use_case.request_email_verification(user.user_id)
                )
                email_data = EmailVerificationData(
                    email=verification_data["email"],
                    user_name=verification_data["user_name"],
                    verification_url=verification_data["verification_url"],
                )
                await send_email_verification.kiq(email_data)  # type: ignore[call-overload]

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
    auth_use_case: AuthUseCaseDep,
):
    refresh_data = token_verification.model_dump(exclude_unset=True)

    try:
        token_pair = await auth_use_case.refresh(refresh_data)
    except RefreshTokenNotFoundError as e:
        logger.exception(
            "Refresh token not found for user_id: %s", token_verification.user_id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from e
    except RefreshTokenCompromisedError:
        logger.info(
            "Refresh token was compromised for user_id: %s", token_verification.user_id
        )
        # TODO: add force logout.

    except UserNotFoundError as e:
        logger.debug("User with id %s was not found", token_verification.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to authorize",
        ) from e

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
    else:
        return token_pair


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    logout_request: LogoutRequest,
    auth_use_case: AuthUseCaseDep,
):
    try:
        # TODO: remove refresh_token from logout method and
        # remove all tokens for required device.
        await auth_use_case.logout(
            user_id=logout_request.user_id,
            refresh_token=logout_request.refresh_token,
            fingerprint=logout_request.fingerprint,
        )
    except UserNotFoundError as e:
        logger.debug("User %s not found during logout", logout_request.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from e
    except RefreshTokenNotFoundError:
        logger.debug(
            "Refresh token not found for user %s during logout", logout_request.user_id
        )
        return None
    except RevokeRefreshTokenError as e:
        logger.exception(
            "Failed to revoke refresh token for user %s: %s",
            logout_request.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout due to a technical issue. Please try again later.",
        ) from e


@router.put("/password", response_model=PasswordUpdateResponse)
async def update_password(
    password_data: PasswordUpdate,
    current_user: CurrentVerifiedUserDep,
    password_use_case: PasswordUseCaseDep,
):
    """Change password for authenticated user."""
    try:
        await password_use_case.update_password(
            user_id=current_user.user_id,
            old_password=password_data.old_password,
            new_password=password_data.new_password,
        )
    except UserAuthenticationError as e:
        logger.exception(
            "Password change failed for user %s: incorrect current password",
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from e
    return PasswordUpdateResponse(message="Password has been successfully updated.")


@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    password_use_case: PasswordUseCaseDep,
):
    result = await password_use_case.request_password_reset(request_data.email)

    if result is not None:
        with contextlib.suppress(Exception):
            email_data = PasswordResetEmailData(
                email=result["email"],
                user_name=result["user_name"],
                reset_url=result["reset_url"],
            )
            await send_password_reset_email.kiq(email_data)  # type: ignore[call-overload]

    return PasswordResetResponse(message="Password has been successfully reset.")


@router.post("/password-reset/confirm", response_model=PasswordResetResponse)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    password_use_case: PasswordUseCaseDep,
):
    try:
        result = await password_use_case.confirm_password_reset(
            confirm_data.token,
            confirm_data.new_password,
        )

        with contextlib.suppress(Exception):
            await send_password_changed_email.kiq(  # type: ignore[call-overload]
                email=result["email"],
                user_name=result["user_name"],
            )
    except InvalidPasswordResetTokenError as e:
        logger.exception("Password reset attempt with invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token",
        ) from e
    except ExpiredPasswordResetTokenError as e:
        logger.exception("Password reset attempt with expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one.",
        ) from e

    return PasswordResetResponse(message="Password has been successfully reset.")


@router.post(
    "/email-verification",
    response_model=EmailVerificationSendResponse,
)
async def send_verification_email(
    current_user: CurrentUserRequiredDep,
    verification_use_case: VerificationUseCaseDep,
):
    """Send email verification email to currently authenticated user."""
    try:
        verification_data = await verification_use_case.request_email_verification(
            current_user.user_id
        )

        with contextlib.suppress(Exception):
            email_data = EmailVerificationData(
                email=verification_data["email"],
                user_name=verification_data["user_name"],
                verification_url=verification_data["verification_url"],
            )
            await send_email_verification.kiq(email_data)  # type: ignore[call-overload]
    except EmailAlreadyVerifiedError as e:
        logger.debug(
            "User %s attempted to verify already verified email",
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified.",
        ) from e
    except Exception as e:
        logger.exception(
            "Failed to send verification email for user %s",
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email.",
        ) from e

    return EmailVerificationSendResponse(message="Verification email has been sent.")


@router.post(
    "/email-verification/confirm",
    response_model=EmailVerificationResponse,
)
async def confirm_email_verification(
    verification_request: EmailVerificationConfirm,
    verification_use_case: VerificationUseCaseDep,
):
    """Confirm email verification using verification token."""
    try:
        await verification_use_case.confirm_email_verification(
            verification_request.token
        )
    except InvalidEmailVerificationTokenError as e:
        logger.debug("Email verification attempt with invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token.",
        ) from e
    except ExpiredEmailVerificationTokenError as e:
        logger.debug("Email verification attempt with expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired.",
        ) from e
    except EmailAlreadyVerifiedError as e:
        logger.debug("Email verification attempt for already verified email")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified.",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error during email verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed.",
        ) from e

    return EmailVerificationResponse(message="Email has been successfully verified.")
