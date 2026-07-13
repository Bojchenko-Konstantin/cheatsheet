import hashlib
import hmac
from dataclasses import dataclass
from uuid import UUID

from src.application.dto.oauth import OAuthService
from src.core.config import settings


@dataclass(slots=True, kw_only=True)
class OAuthUserCreationData:
    provider_user_id: str | int
    provider_psuid: str | None = None
    user_name: str | None
    email: str
    oauth_service_id: OAuthService
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None

    def __post_init__(self):
        if self.name and self.name.strip():
            name_parts = self.name.split(maxsplit=1)

            if len(name_parts) > 1:
                self.first_name, self.last_name = name_parts
            else:
                self.first_name = name_parts[0]

        if not self.provider_psuid and self.oauth_service_id in (
            OAuthService.GITHUB,
            OAuthService.GOOGLE,
        ):
            message = (
                f"{self.provider_user_id}:{settings.github_oauth.client_id}".encode()
            )
            self.provider_psuid = self._hash(message)

        self.provider_user_id = str(self.provider_user_id)

        if not self.user_name:
            self.user_name = self.email.split("@")[0]

    @staticmethod
    def _hash(message: bytes):
        return hmac.new(
            key=settings.oauth.psuid_secret.encode(),
            msg=message,
            digestmod=hashlib.sha256,
        ).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class OAuthAccountLinkingData:
    provider_user_id: str
    provider_psuid: str
    oauth_service_id: OAuthService


@dataclass(frozen=True, slots=True, kw_only=True)
class OAuthUserAccount:
    oauth_account_id: UUID
    user_id: UUID
    oauth_service_name: str
    oauth_service_id: int
    user_name: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
