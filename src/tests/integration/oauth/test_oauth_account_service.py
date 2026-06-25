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
        psuid="test_psuid",
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
    expected_user_id = await _get_user_id_by_provider_user_id(
        session, test_user_info["id"]
    )

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
        psuid="update_hash_test_psuid",
        default_email="test_update_token@email.com",
        login="test_update_token",
    )
    data = dict(
        provider_user_id="987654321",
        provider_psuid="update_hash_test_psuid",
        email="test_update_token@email.com",
        user_name="test_update_token",
        hashed_token="old_hashed_token",
        oauth_service_id=OAuthService.YANDEX,
    )
    oauth_account_id, original_hash, _ = await _prepare_oauth_account(session, data)
    await session.commit()

    sut = OAuthAccountService()

    # Act.
    user_id = await sut.process_oauth_login(
        plain_refresh_token=plain_refresh_token,
        user_info=test_user_info,
        oauth_service_id=OAuthService.YANDEX,
    )
    expected_user_id, new_hash = await _get_active_token_info_by_account_id(
        session, oauth_account_id
    )

    # Assert.
    assert new_hash != original_hash
    assert user_id == expected_user_id


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_process_oauth_login_existing_user_link_new_provider(
    session: AsyncSession,
):
    # Arrange
    shared_email = "shared_user@email.com"
    plain_refresh_token = "github_refresh_token"
    new_oauth_service = OAuthService.GITHUB

    test_user_info = {
        "id": "github_user_id_123",
        "psuid": "github_psuid_abc",
        "default_email": shared_email,
        "login": "github_login",
    }

    existing_user_data = {
        "provider_user_id": "yandex_user_id_789",
        "provider_psuid": "yandex_psuid_xyz",
        "email": shared_email,
        "user_name": "yandex_login",
        "hashed_token": "yandex_hashed_token",
        "oauth_service_id": OAuthService.YANDEX,
    }

    oauth_account_id, _, _ = await _prepare_oauth_account(session, existing_user_data)
    await session.commit()

    expected_user_id = await _get_user_id_by_account_id(session, oauth_account_id)
    sut = OAuthAccountService()

    # Act
    returned_user_id = await sut.process_oauth_login(
        plain_refresh_token=plain_refresh_token,
        user_info=test_user_info,
        oauth_service_id=new_oauth_service,
    )

    is_new_service_linked = await _is_service_linked_to_user(
        session=session,
        user_id=expected_user_id,
        oauth_service_id=new_oauth_service.value,
    )

    # Assert
    assert returned_user_id == expected_user_id
    assert is_new_service_linked is True


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_process_oauth_login_when_user_sign_up_with_existing_user_name(
    session: AsyncSession,
):
    # Arrange.
    plain_refresh_token = "test_hash"
    test_user_info = dict(
        id="1234567890",
        psuid="test_psuid",
        default_email="test@email.com",
        login="repeated_login",
    )
    existing_user_data = {
        "provider_user_id": "yandex_user_id",
        "provider_psuid": "yandex_psuid",
        "email": "different@email.com",
        "user_name": "repeated_login",
        "hashed_token": "yandex_hashed_token",
        "oauth_service_id": OAuthService.YANDEX,
    }

    await _prepare_oauth_account(session, existing_user_data)
    await session.commit()

    sut = OAuthAccountService()

    # Act.
    returned_user_id = await sut.process_oauth_login(
        plain_refresh_token=plain_refresh_token,
        user_info=test_user_info,
        oauth_service_id=OAuthService.YANDEX,
    )
    user_name = await _get_user_name_by_user_id(session, returned_user_id)

    # Assert.
    assert user_name != test_user_info["login"]


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_unlink_account(session: AsyncSession):
    # Arrange.
    user_data_yandex = {
        "provider_user_id": "yandex_user_id_345",
        "provider_psuid": "yandex_psuid_abcd",
        "email": "test@email.com",
        "user_name": "yandex_login",
        "hashed_token": "yandex_hashed_token",
        "oauth_service_id": OAuthService.YANDEX,
    }
    user_data_github = {
        "provider_user_id": "github_user_id_543",
        "provider_psuid": "github_psuid_dcba",
        "email": "test@email.com",
        "user_name": "github_login",
        "hashed_token": "github_hashed_token",
        "oauth_service_id": OAuthService.GITHUB,
    }

    _, _, user_id = await _prepare_oauth_account(session, user_data_yandex)
    await session.commit()

    await _add_second_oauth_account(session, user_id, user_data_github)
    await session.commit()

    current_account_amount = await _count_user_accounts(session, user_id)
    assert current_account_amount == 2

    sut = OAuthAccountService()

    # Act.
    await sut.unlink_oauth_account(user_id, OAuthService.YANDEX)
    await session.commit()

    result_account_amount = await _count_user_accounts(session, user_id)

    # Assert.
    assert result_account_amount == 1


async def _count_user_accounts(session: AsyncSession, user_id: UUID) -> int:
    query = text(
        """
        SELECT COUNT(oauth_account_id) AS result
        FROM "user"
        JOIN oauth_account USING (user_id)
        WHERE user_id = :user_id
        """
    )

    result = await session.execute(query, {"user_id": user_id})
    db_row = result.one()
    return db_row.result


async def _add_second_oauth_account(
    session: AsyncSession, user_id: UUID, data: dict[str, Any]
):
    """Add second OAuth account for existing user."""
    oauth_account_id = await _insert_oauth_account(
        session=session,
        user_id=user_id,
        provider_user_id=data["provider_user_id"],
        provider_psuid=data["provider_psuid"],
        oauth_service_id=data["oauth_service_id"],
    )
    await _insert_refresh_token(session, oauth_account_id, data["hashed_token"])
    return user_id


async def _get_user_name_by_user_id(session: AsyncSession, user_id: UUID) -> str:
    """Retrieves the internal user ID using their external OAuth provider user ID."""
    query = text(
        """
        SELECT user_name
        FROM "user"
        WHERE user_id = :user_id
        """
    )

    result = await session.execute(query, {"user_id": user_id})
    db_row = result.one()
    return db_row.user_name


async def _get_user_id_by_provider_user_id(
    session: AsyncSession, provider_user_id: str
) -> UUID:
    """Retrieves the internal user ID using their external OAuth provider user ID."""
    query = _build_select_user_id_query()
    result = await session.execute(query, {"provider_user_id": provider_user_id})
    db_row = result.one()
    return db_row.user_id


def _build_select_user_id_query() -> TextClause:
    """Builds the SQL query to find a user_id based on provider_user_id."""
    return text(
        """
        SELECT user_id
        FROM oauth_account
        WHERE provider_user_id = :provider_user_id
        """
    )


async def _prepare_oauth_account(session: AsyncSession, data: dict[str, Any]):
    """
    Prepares the database environment by creating a user,
    an OAuth account, and a refresh token.
    """
    user_id = await _insert_user(session, data["user_name"], data["email"])
    oauth_account_id = await _insert_oauth_account(
        session=session,
        user_id=user_id,
        provider_user_id=data["provider_user_id"],
        provider_psuid=data["provider_psuid"],
        oauth_service_id=data["oauth_service_id"],
    )
    refresh_token_hash = await _insert_refresh_token(
        session, oauth_account_id, data["hashed_token"]
    )
    return oauth_account_id, refresh_token_hash, user_id


async def _insert_user(session: AsyncSession, user_name: str, email: str) -> UUID:
    """Inserts a new user record into the "user" table."""
    query = text(
        """
        INSERT INTO "user"(user_name, email, is_active) VALUES
        (:user_name, :email, True)
        RETURNING user_id
        """
    )
    result = await session.execute(query, {"user_name": user_name, "email": email})
    return result.one().user_id


async def _insert_oauth_account(
    session: AsyncSession,
    user_id: UUID,
    provider_user_id: str,
    provider_psuid: str,
    oauth_service_id: OAuthService,
) -> UUID:
    """Links an external OAuth provider account to an internal user record."""
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


async def _insert_refresh_token(
    session: AsyncSession, oauth_account_id: UUID, hashed_token: str
) -> str:
    """Saves a hashed refresh token for the specified OAuth account in the database."""
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


async def _get_active_token_info_by_account_id(
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


async def _get_user_id_by_account_id(
    session: AsyncSession, oauth_account_id: UUID
) -> UUID:
    query = text(
        """
        SELECT user_id
        FROM oauth_account
        WHERE oauth_account_id = :oauth_account_id
        """
    )

    result = await session.execute(query, {"oauth_account_id": oauth_account_id})

    return result.one().user_id


async def _is_service_linked_to_user(
    session: AsyncSession, user_id: UUID, oauth_service_id: int
) -> bool:
    """Checks whether a specific OAuth provider is linked to the given user."""

    query = text(
        """
        SELECT EXISTS (
            SELECT FROM oauth_account
            WHERE user_id = :user_id AND oauth_service_id = :oauth_service_id
        )
        """
    )

    result = await session.execute(
        query, {"user_id": user_id, "oauth_service_id": oauth_service_id}
    )

    return result.scalar_one()
