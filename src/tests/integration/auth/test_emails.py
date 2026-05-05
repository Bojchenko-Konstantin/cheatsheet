import json

import pytest
from httpx import AsyncClient

from src.tests.integration.auth.conftest import TEST_PASSWORD

MAILHOG = "http://localhost:8025"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_emails_were_sent_successfully_when_register(
    populate_db_for_multiple_users: None, async_client: AsyncClient
):
    # Arrange.
    data_for_register = {
        "username": "test_email",
        "email": "test-email@example.com",
        "first_name": "string",
        "last_name": "string",
        "profile_description": "string",
        "image_url": "string",
        "social_network_id": [0],
        "network_url": ["string"],
        "password": TEST_PASSWORD,
        "password_confirmation": TEST_PASSWORD,
    }

    # Act.
    await async_client.post("/register", json=data_for_register)
    async with AsyncClient() as client:
        email = await client.get(
            f"{MAILHOG}/api/v2/search?kind=from&query=sender@test.com"
        )

    email_content = email.content.decode()
    json_email_content = json.loads(email_content)

    verification_email_content = json_email_content["items"][0]["Raw"]["Data"]
    welcome_email_content = json_email_content["items"][1]["Raw"]["Data"]

    # Assert.
    assert welcome_email_content == "Hello, test"
    assert verification_email_content == "Test email verification"
