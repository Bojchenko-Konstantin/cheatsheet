from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.token import TokenStatus
from src.infrastructure.dto import OAuthService
from src.infrastructure.services.oauth import OAuthAccountService


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_process_oauth_login_new_user_sign_up(session: AsyncSession):
    # Arrange.
    plain_refresh_token = "test_hash"
    test_user_info = dict(
        id="1234567890",
        psuid="3.BBodb.Gnes5pBRaO7MusadkV7r8U2A.FG77AksboyRm0oaKSaD8298vlaKD24",
        default_email="test@email.com",
        login="test",
    )
    sut = OAuthAccountService()

    # Act.
    result = await sut.process_oauth_login(
        plain_refresh_token=plain_refresh_token,
        user_info=test_user_info,
        oauth_service_id=OAuthService.YANDEX,
    )
    expected_user_id = await _get_user_id_from_db(session, test_user_info["id"])

    # Assert.
    assert result == expected_user_id


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_process_oauth_login_when_user_refresh_token(
    session: AsyncSession,
):
    # Arrange.
    plain_refresh_token = "updated_hash"
    test_user_info = dict(
        id="987654321",
        psuid="3.BBo8b.Gnas7pBRaO7MusadkV7r0U9A.FG78AksboyR0moaKSaD8298vlaKD24",
        default_email="test_update_token@email.com",
        login="test_update_token",
    )
    data = dict(
        provider_user_id="987654321",
        provider_psuid="3.BBo8b.Gnas7pBRaO7MusadkV7r0U9A.FG78AksboyR0moaKSaD8298vlaKD24",
        email="test_update_token@email.com",
        user_name="test_update_token",
        hashed_token="old_hashed_token",
        oauth_service_id=OAuthService.YANDEX,
    )
    oauth_account_id, original_hash = await _prepare_oauth_account(session, data)
    await session.commit()

    sut = OAuthAccountService()

    # Act.
    user_id = await sut.process_oauth_login(
        plain_refresh_token=plain_refresh_token,
        user_info=test_user_info,
        oauth_service_id=OAuthService.YANDEX,
    )
    expected_user_id, new_hash = await _get_new_hash_from_db(session, oauth_account_id)

    # Assert.
    assert new_hash != original_hash
    assert user_id == expected_user_id


async def _get_user_id_from_db(session: AsyncSession, provider_user_id: str):
    query = _build_select_user_id_query()
    result = await session.execute(query, {"provider_user_id": provider_user_id})
    db_row = result.one()
    return db_row.user_id


def _build_select_user_id_query() -> TextClause:
    return text(
        """
        SELECT user_id
        FROM oauth_account
        WHERE provider_user_id = :provider_user_id
        """
    )


async def _prepare_oauth_account(session: AsyncSession, data: dict[str, Any]):
    user_id = await _insert_user_data(session, data["user_name"], data["email"])
    oauth_account_id = await _insert_oauth_account_data(
        session=session,
        user_id=user_id,
        provider_user_id=data["provider_user_id"],
        provider_psuid=data["provider_psuid"],
        oauth_service_id=data["oauth_service_id"],
    )
    refresh_token_hash = await _insert_refresh_token_data(
        session, oauth_account_id, data["hashed_token"]
    )
    return oauth_account_id, refresh_token_hash


async def _insert_user_data(session: AsyncSession, user_name: str, email: str) -> UUID:
    query = text(
        """
        INSERT INTO "user"(user_name, email, is_active) VALUES
        (:user_name, :email, True)
        RETURNING user_id
        """
    )
    result = await session.execute(query, {"user_name": user_name, "email": email})
    return result.one().user_id


async def _insert_oauth_account_data(
    session: AsyncSession,
    user_id: UUID,
    provider_user_id: str,
    provider_psuid: str,
    oauth_service_id: OAuthService,
) -> UUID:
    query = text(
        """
        INSERT INTO oauth_account(user_id, provider_user_id,
                                  provider_psuid, oauth_service_id) VALUES
        (:user_id, :provider_user_id, :provider_psuid, :oauth_service_id)
        RETURNING oauth_account_id
        """
    )
    result = await session.execute(
        query,
        {
            "user_id": user_id,
            "provider_user_id": provider_user_id,
            "provider_psuid": provider_psuid,
            "oauth_service_id": oauth_service_id,
        },
    )
    return result.one().oauth_account_id


async def _insert_refresh_token_data(
    session: AsyncSession, oauth_account_id: UUID, hashed_token: str
) -> str:
    query = text(
        """
    INSERT INTO oauth_refresh_token(oauth_account_id, status_id, hashed_token) VALUES
    (:oauth_account_id, :status_id, :hashed_token)
    RETURNING hashed_token
    """
    )
    result = await session.execute(
        query,
        {
            "oauth_account_id": oauth_account_id,
            "status_id": TokenStatus.ACTIVE,
            "hashed_token": hashed_token,
        },
    )
    return result.one().hashed_token


async def _get_new_hash_from_db(
    session: AsyncSession, oauth_account_id: UUID
) -> tuple[UUID, str]:
    query = text(
        """
        SELECT user_id, hashed_token
        FROM oauth_refresh_token
        JOIN oauth_account USING (oauth_account_id)
        WHERE oauth_account_id = :oauth_account_id
        AND status_id = 1
        """
    )
    result = await session.execute(query, {"oauth_account_id": oauth_account_id})
    db_row = result.one()
    return db_row.user_id, db_row.hashed_token
