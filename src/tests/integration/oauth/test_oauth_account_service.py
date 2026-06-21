import pytest
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.dto import OAuthService
from src.infrastructure.services.oauth import OAuthAccountService


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_process_oauth_login_when_user_sign_up_for_the_first_time(
    session: AsyncSession,
):
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

    # Assesrt.
    assert result == expected_user_id


async def _get_user_id_from_db(session: AsyncSession, provider_user_id: str):
    query = _build_query()
    result = await session.execute(query, {"provider_user_id": provider_user_id})
    db_row = result.one()
    return db_row.user_id


def _build_query() -> TextClause:
    return text(
        """
        SELECT user_id
        FROM oauth_account
        WHERE provider_user_id = :provider_user_id
        """
    )
