from dataclasses import dataclass
from uuid import UUID

from src.application.dto.oauth import OAuthService


@dataclass(slots=True, kw_only=True)
class OAuthUserCreationData:
    provider_user_id: str
    provider_psuid: str
    user_name: str
    email: str
    oauth_service_id: OAuthService
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None

    def __post_init__(self):
        if self.name:
            self.first_name, self.last_name = self.name.split(maxsplit=1)


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
