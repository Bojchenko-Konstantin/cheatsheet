from argon2 import Type
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

HASHER: PasswordHash = PasswordHash(
    [
        Argon2Hasher(
            type=Type.ID,
            time_cost=2,
            memory_cost=19456,
            parallelism=1,
            hash_len=32,
            salt_len=16,
        )
    ]
)
