import logging
from uuid import UUID

from src.application.dto.oauth import OAuthService
from src.application.exceptions import UnlinkLastOAuthAccountError
from src.application.interfaces import IOAuthAccountService
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.dto import (
    OAuthAccountLinkingData,
    OAuthUserAccount,
    OAuthUserCreationData,
)

logger = logging.getLogger(__name__)


class OAuthAccountService(IOAuthAccountService):
    """Handles all operations with OAuth account."""

    def __init__(self, unit_of_work: SQLAlchemyUnitOfWork | None = None):
        self._unit_of_work = unit_of_work or SQLAlchemyUnitOfWork()

    async def process_oauth_login(
        self,
        user_info: dict[str, str],
        oauth_service_id: OAuthService,
    ) -> UUID:
        """
        Process the OAuth authentication flow for a user.

        This method orchestrates the entire login/registration workflow via OAuth:
        2. Normalizes user profile data.
        3. Identifies whether the user already exists by their email.
        4. Links a new service to the existing user, or registers a brand new user.
        """
        save_data = self._get_data_to_save(user_info, oauth_service_id)

        # TODO: add image url processing (download and save).

        try:
            existing_accounts = await self._try_to_get_existing_accounts(
                save_data.email
            )

            if existing_accounts:
                return await self._process_existing_user(
                    existing_accounts, oauth_service_id, save_data
                )

            return await self._register_new_user(save_data)
        except Exception as e:
            logger.exception(
                f"Failed to process OAuth login for email {save_data.email}: {str(e)}"
            )
            raise

    async def unlink_oauth_account(self, user_id: UUID, oauth_service_id: OAuthService):
        """Unlinks a specific OAuth service from the user's account."""
        if not await self._can_unlink_account(user_id):
            raise UnlinkLastOAuthAccountError

        await self._unlink_account(user_id, oauth_service_id)

    def _get_data_to_save(
        self, user_info: dict[str, str], oauth_service_id: OAuthService
    ) -> OAuthUserCreationData:
        return OAuthUserCreationData(
            provider_user_id=user_info.get("id") or user_info["sub"],
            oauth_service_id=oauth_service_id,
            provider_psuid=user_info.get("psuid"),
            email=user_info["email"],
            user_name=user_info.get("login"),
            name=user_info.get("name"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
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
        save_data: OAuthUserCreationData,
    ):
        """Link new account to existing user."""
        user_id = existing_accounts[0].user_id

        matched_account = next(
            (
                account
                for account in existing_accounts
                if account.oauth_service_id == oauth_service_id
            ),
            None,
        )

        if not matched_account:
            await self._link_new_service(user_id, save_data)

        return user_id

    async def _register_new_user(self, save_data: OAuthUserCreationData):
        async with self._unit_of_work as uow:
            user_id = await uow.oauth_repo.save(save_data)
            return user_id

    async def _link_new_service(self, user_id: UUID, save_data: OAuthUserCreationData):
        linking_data = self._map_creation_to_linking(save_data)
        async with self._unit_of_work as uow:
            await uow.oauth_repo.link_new_service(user_id, linking_data)

    async def _can_unlink_account(self, user_id: UUID) -> bool:
        """
        Checks if the user has other authentication methods left
        to allow unlinking.
        """
        async with self._unit_of_work.readonly() as uow:
            (
                hashed_password,
                account_count,
            ) = await uow.oauth_repo.get_user_with_oauth_accounts(user_id)
            return hashed_password is not None or account_count > 1

    async def _unlink_account(
        self, user_id: UUID, oauth_service_id: OAuthService
    ) -> None:
        async with self._unit_of_work as uow:
            await uow.oauth_repo.unlink_account(user_id, oauth_service_id)

    @staticmethod
    def _map_creation_to_linking(creation_data: OAuthUserCreationData):
        return OAuthAccountLinkingData(
            provider_user_id=creation_data.provider_user_id,
            provider_psuid=creation_data.provider_psuid,
            oauth_service_id=creation_data.oauth_service_id,
        )
