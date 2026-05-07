from dataclasses import dataclass

from src.infrastructure.hasher import HASHER


@dataclass(slots=True)
class DBUserData:
    name: str
    password: str = "Passw0rd%"
    hashed_password: str = ""
    email: str = ""
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = True

    def __post_init__(self):
        if not self.hashed_password:
            self.hashed_password = HASHER.hash(self.password)

        if not self.email:
            self.email = self.name + "@test.com"
