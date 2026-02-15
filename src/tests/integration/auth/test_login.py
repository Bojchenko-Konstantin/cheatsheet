import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login(
    populate_db_for_single_user: None,
    async_client: AsyncClient,
):
    data_for_login = {
        "username": "test",
        "password": "password",
    }

    response = await async_client.post("/login", data=data_for_login)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert {"access_token", "refresh_token", "token_type"} == response_data.keys()
    assert response_data["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_login_was_unsuccessful(
    populate_db_for_single_user: None,
    async_client: AsyncClient,
):
    data_for_login = {
        "username": "random",
        "password": "password",
    }

    response = await async_client.post("/login", data=data_for_login)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
