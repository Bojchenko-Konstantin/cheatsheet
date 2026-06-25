from dataclasses import dataclass
from enum import IntEnum
from uuid import UUID


class OAuthService(IntEnum):
    YANDEX = 1
    GITHUB = 2


@dataclass(frozen=True, slots=True, kw_only=True)
class OAuthUserCreationData:
    provider_user_id: str
    provider_psuid: str
    user_name: str
    email: str
    oauth_service_id: OAuthService
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None


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
