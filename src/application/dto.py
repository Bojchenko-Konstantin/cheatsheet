from collections.abc import MutableMapping
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Self
from uuid import UUID


@dataclass(slots=True)
class User:
    user_id: UUID
    user_name: str
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool

    @classmethod
    def from_dict(cls, kwargs: MutableMapping) -> Self:
        return cls(**kwargs)


@dataclass(slots=True)
class UserPayload:
    user_id: str
    is_superuser: bool
    exp: datetime | None = None

    @classmethod
    def from_dict(cls, kwargs: MutableMapping) -> Self:
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return asdict(self)
