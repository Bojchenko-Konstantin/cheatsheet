from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import (
    OAuthAccountModel,
    OAuthRefreshTokenModel,
    UserModel,
)
from src.infrastructure.dto import OAuthUserCreationData


class SQLAlchemyOAuthRepo:
    """Class for operations with OAuth that interact with database using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, refresh_token_hash: str, save_data: OAuthUserCreationData):
        model = UserModel(user_name=save_data.user_name, email=save_data.email)
        model.oauth_account = OAuthAccountModel(
            provider_user_id=save_data.provider_user_id,
            provider_psuid=save_data.provider_psuid,
            oauth_service_id=save_data.oauth_service_id,
        )

        refresh_token = OAuthRefreshTokenModel(hashed_token=refresh_token_hash)
        model.oauth_account.refresh_tokens.append(refresh_token)
        self._session.add(model)

        try:
            await self._session.flush()
        except Exception:
            # TODO: add custom Exception
            raise
