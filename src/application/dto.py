from collections.abc import MutableMapping
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class UserPayload:
    user_id: UUID
    is_superuser: bool
