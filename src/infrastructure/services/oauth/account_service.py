import logging
from uuid import UUID

from cryptography.fernet import Fernet

from src.core.config import settings
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.dto import (
    OAuthService,
    OAuthUserAccount,
    OAuthUserCreationData,
)

logger = logging.getLogger(__name__)


class OAuthAccountService:
    """Handles all operations with OAuth refresh tokens."""

    def __init__(self, unit_of_work: SQLAlchemyUnitOfWork | None = None):
        self._unit_of_work = unit_of_work or SQLAlchemyUnitOfWork()
        self._cipher = Fernet(settings.general_oauth.refresh_token_encryption_key)

    async def process_oauth_login(
        self,
        plain_refresh_token: str,
        user_info: dict[str, str],
        oauth_service_id: OAuthService,
    ) -> UUID:
        refresh_token_hash = self._generate_refresh_token_hash(plain_refresh_token)
        save_data = self._get_data_to_save(user_info, oauth_service_id)

        try:
            existing_accounts = await self._try_to_get_existing_accounts(
                save_data.email
            )

            if existing_accounts:
                return await self._process_existing_user(
                    existing_accounts, oauth_service_id, refresh_token_hash, save_data
                )

            return await self._register_new_user(refresh_token_hash, save_data)
        except Exception as e:
            logger.exception(
                f"Failed to process OAuth login for email {save_data.email}: {str(e)}"
            )
            raise

    async def _update_existing_provider(
        self, oauth_account_id: UUID, refresh_token_hash: str
    ):
        async with self._unit_of_work as uow:
            await uow.oauth_repo.update_refresh_token(
                oauth_account_id, refresh_token_hash
            )

    def _generate_refresh_token_hash(self, plain_refresh_token: str) -> str:
        return self._cipher.encrypt(plain_refresh_token.encode()).decode()

    def _get_data_to_save(
        self, user_info: dict[str, str], oauth_service_id: OAuthService
    ) -> OAuthUserCreationData:
        return OAuthUserCreationData(
            provider_user_id=user_info["id"],
            oauth_service_id=oauth_service_id,
            provider_psuid=user_info["psuid"],
            email=user_info["default_email"],
            user_name=user_info["login"],
        )

    async def _try_to_get_existing_accounts(
        self, email: str
    ) -> list[OAuthUserAccount] | None:
        async with self._unit_of_work.readonly() as uow:
            accounts = await uow.oauth_repo.get_by_email(email)
            return accounts

    async def _process_existing_user(
        self,
        existing_accounts: list[OAuthUserAccount],
        oauth_service_id: OAuthService,
        refresh_token_hash: str,
        save_data: OAuthUserCreationData,
    ):
        """
        Update current account refresh token or link new account to existing user.
        """
        user_id = existing_accounts[0].user_id

        matched_account = next(
            (
                account
                for account in existing_accounts
                if account.oauth_service_id == oauth_service_id
            ),
            None,
        )

        if matched_account:
            await self._update_existing_provider(
                matched_account.oauth_account_id, refresh_token_hash
            )
        else:
            await self._link_new_service(user_id, refresh_token_hash, save_data)

        return user_id

    async def _register_new_user(
        self, refresh_token_hash: str, save_data: OAuthUserCreationData
    ):
        async with self._unit_of_work as uow:
            user_id = await uow.oauth_repo.save(refresh_token_hash, save_data)
            return user_id

    async def _link_new_service(
        self, user_id: UUID, refresh_token_hash: str, save_data: OAuthUserCreationData
    ):
        async with self._unit_of_work as uow:
            await uow.oauth_repo.link_new_service(
                user_id, refresh_token_hash, save_data
            )
