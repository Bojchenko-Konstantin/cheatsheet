import contextlib
import logging

from fastapi import APIRouter, HTTPException, Request, Response, status

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
    Token,
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
from src.core.config import settings
from src.infrastructure.background_tasks import (
    send_email_verification,
    send_password_changed_email,
    send_password_reset_email,
    send_welcome_email,
)

router = APIRouter(tags=["Authentication"])
logger = logging.getLogger(__name__)

COOKIE_PARAMS = {
    "max_age": settings.jwt.refresh_token_expires_in - 10,
    "httponly": True,
    "secure": True,
    "samesite": "strict",
    "path": "/",
}


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    user_form: OAuth2FormDep,
    auth_use_case: AuthUseCaseDep,
):
    user_login = user_form.username
    try:
        token_pair = await auth_use_case.authenticate(
            user_login=user_login, password=user_form.password
        )
    except UserNotFoundError:
        logger.debug("User with username %s was not found", user_login)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to authorize",
        ) from None
    except UserAuthenticationError:
        logger.debug("Failed login attempt for username: %s", user_login)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid username or password",
        ) from None
    except UserInactiveError:
        logger.warning("Inactive user attempted login: %s", user_login)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Account is inactive",
        ) from None
    except AccessTokenExpiredError as e:
        logger.exception("Access token expired: %s", str(e))

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from None
    except AccessTokenException:
        logger.exception("Failed to generate access token for username: %s", user_login)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authorize. Please try again later.",
        ) from None
    else:
        response.set_cookie(
            key="refresh_token", value=token_pair.refresh_token, **COOKIE_PARAMS
        )

        return {"access_token": token_pair.access_token}


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
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
                user = await auth_use_case.get_current_user(token_pair.access_token)
                verification_data = (
                    await verification_use_case.request_email_verification(user.user_id)
                )
                email_data = EmailVerificationData(
                    email=verification_data["email"],
                    user_name=verification_data["user_name"],
                    verification_url=verification_data["verification_url"],
                )

                await send_email_verification.kiq(email_data)  # type: ignore[call-overload]

    except DuplicateUserError:
        logger.debug(
            "User registration failed - username '%s' already exists.",
            user_form.username,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username '{user_form.username}' already exists. "
            "Please choose another one.",
        ) from None
    except UserCreationError:
        logger.exception(
            "Unexpected error during user registration for username: %s",
            user_form.username,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration. "
            "Please try again later.",
        ) from None
    except AccessTokenExpiredError as e:
        logger.exception("Access token expired: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from None
    except AccessTokenException:
        logger.exception(
            "Failed to generate access token for username: %s", user_form.username
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authorize. Please try again later.",
        ) from None
    else:
        response.set_cookie(
            key="refresh_token", value=token_pair.refresh_token, **COOKIE_PARAMS
        )

        return {"access_token": token_pair.access_token}


@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    token_verification: TokenVerification,
    auth_use_case: AuthUseCaseDep,
):
    refresh_data = token_verification.model_dump(exclude_unset=True)
    refresh_token = request.cookies.get("refresh_token")
    refresh_data["refresh_token"] = refresh_token

    try:
        token_pair = await auth_use_case.refresh(refresh_data)
    except RefreshTokenNotFoundError:
        logger.exception("Refresh token not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from None
    except RefreshTokenCompromisedError:
        logger.info("Refresh token was compromised")
        response.delete_cookie("refresh_token", path=COOKIE_PARAMS["path"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from None
    except UserNotFoundError as e:
        logger.debug("User with id %s was not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to authorize. Error: {str(e)}",
        ) from None
    except AccessTokenExpiredError as e:
        logger.exception("Access token expired: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Failed to authorize",
        ) from None
    except AccessTokenException as e:
        logger.exception("Failed to generate access token")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authorize. Please try again later. Error: {str(e)}",
        ) from None
    else:
        response.set_cookie(
            key="refresh_token", value=token_pair.refresh_token, **COOKIE_PARAMS
        )

        return {"access_token": token_pair.access_token}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    logout_request: LogoutRequest,
    auth_use_case: AuthUseCaseDep,
):
    logout_data = logout_request.model_dump(exclude_unset=True)
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        logger.debug("Refresh token is missing in cookies during logout request")
        return

    try:
        await auth_use_case.logout(
            refresh_token=refresh_token,
            hashed_fingerprint=logout_data["hashed_fingerprint"],
        )
    except RefreshTokenNotFoundError:
        logger.debug("Refresh token not found during logout")
        return
    except RevokeRefreshTokenError as e:
        logger.exception("Failed to revoke refresh token: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Failed to logout due to a technical issue. "
                f"Please try again later. Error: {str(e)}",
            ),
        ) from None
    finally:
        response.delete_cookie("refresh_token", path=COOKIE_PARAMS["path"])


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
    except UserAuthenticationError:
        logger.exception(
            "Password change failed for user %s: incorrect current password",
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from None

    return PasswordUpdateResponse(message="Password has been successfully updated.")


@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    password_use_case: PasswordUseCaseDep,
):
    result = await password_use_case.request_password_reset(request_data.email)

    if result is not None:
        email_data = PasswordResetEmailData(
            email=result["email"],
            user_name=result["user_name"],
            reset_url=result["reset_url"],
        )

        with contextlib.suppress(Exception):
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
    except InvalidPasswordResetTokenError:
        logger.exception("Password reset attempt with invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token",
        ) from None
    except ExpiredPasswordResetTokenError:
        logger.exception("Password reset attempt with expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one.",
        ) from None

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
        email_data = EmailVerificationData(
            email=verification_data["email"],
            user_name=verification_data["user_name"],
            verification_url=verification_data["verification_url"],
        )

        with contextlib.suppress(Exception):
            await send_email_verification.kiq(email_data)  # type: ignore[call-overload]
    except EmailAlreadyVerifiedError:
        logger.debug(
            "User %s attempted to verify already verified email",
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified.",
        ) from None
    except Exception as e:
        logger.exception(
            "Failed to send verification email for user %s",
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email. Error: {str(e)}",
        ) from None

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
    except InvalidEmailVerificationTokenError:
        logger.debug("Email verification attempt with invalid token")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token.",
        ) from None
    except ExpiredEmailVerificationTokenError:
        logger.debug("Email verification attempt with expired token")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired.",
        ) from None
    except EmailAlreadyVerifiedError:
        logger.debug("Email verification attempt for already verified email")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified.",
        ) from None
    except Exception as e:
        logger.exception("Unexpected error during email verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed. Error: {str(e)}",
        ) from None
    return EmailVerificationResponse(message="Email has been successfully verified.")
