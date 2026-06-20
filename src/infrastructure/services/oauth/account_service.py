from uuid import UUID

from cryptography.fernet import Fernet

from src.core.config import settings
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.dto import OAuthProvider, OAuthUserCreationData


class OAuthAccountService:
    """Handles all operations with OAuth refresh tokens."""

    def __init__(
        self,
        unit_of_work: SQLAlchemyUnitOfWork = SQLAlchemyUnitOfWork(),
    ):
        self._unit_of_work = unit_of_work
        self._cipher = Fernet(settings.general_oauth.refresh_token_encryption_key)

    async def save_account_with_refresh_token(
        self, plain_refresh_token: str, user_info: dict[str, str]
    ) -> UUID:
        refresh_token_hash = self._generate_refresh_token_hash(plain_refresh_token)
        save_data = self._get_data_to_save(user_info)

        async with self._unit_of_work as uow:
            user_id = await uow.oauth_repo.save(refresh_token_hash, save_data)

        return user_id

    def _generate_refresh_token_hash(self, plain_refresh_token: str) -> str:
        return self._cipher.encrypt(plain_refresh_token.encode()).decode()

    def _get_data_to_save(self, user_info: dict[str, str]) -> OAuthUserCreationData:
        return OAuthUserCreationData(
            provider_user_id=user_info["id"],
            oauth_service_id=OAuthProvider.YANDEX,
            provider_psuid=user_info["psuid"],
            email=user_info["default_email"],
            user_name=user_info["login"],
        )
