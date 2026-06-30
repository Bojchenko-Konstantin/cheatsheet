from abc import abstractmethod
from uuid import UUID

from src.application.dto.oauth import OAuthService


class IOAuthAccountService:
    @abstractmethod
    async def process_oauth_login(
        self, user_info: dict[str, str], oauth_service_id: OAuthService
    ) -> UUID:
        pass

    @abstractmethod
    async def unlink_oauth_account(self, user_id: UUID, oauth_service_id: OAuthService):
        pass
