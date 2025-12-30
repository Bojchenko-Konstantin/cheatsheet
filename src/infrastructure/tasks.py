from uuid import UUID

from src.application.hasher import HASHER
from src.infrastructure.broker import BROKER
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@BROKER.task
async def verify_token_was_not_compromised(
    user_id: UUID,
    fingerprint: str,
    plain_refresh_token: str,
) -> None:
    uow = SQLAlchemyUnitOfWork()
    async with uow:
        tokens = await uow.jwt_repo.get_device_blacklisted_token_family(
            user_id, fingerprint
        )

        if tokens:
            for token in tokens:
                if HASHER.verify(plain_refresh_token, token.hashed_token):
                    await uow.jwt_repo.mark_tokens_as_compromised(
                        user_id=user_id,
                        fingerprint=fingerprint,
                    )
