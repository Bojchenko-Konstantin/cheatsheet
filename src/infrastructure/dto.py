from dataclasses import dataclass
from enum import IntEnum


class OAuthProvider(IntEnum):
    YANDEX = 1
    GITHUB = 2


@dataclass(frozen=True, slots=True, kw_only=True)
class OAuthUserCreationData:
    provider_user_id: str
    provider_psuid: str
    user_name: str
    email: str
    oauth_service_id: OAuthProvider
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
