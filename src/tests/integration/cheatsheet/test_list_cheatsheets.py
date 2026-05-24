import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_first_page_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=2")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 2
    assert response_data["has_next"] is True
    assert response_data["next_cursor"] is not None


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_second_page_with_cursor_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    # Arrange.
    first_response = await async_client.get("/cheatsheets/?size=2")
    first_data = first_response.json()
    cursor = first_data["next_cursor"]

    # Act.
    response = await async_client.get(f"/cheatsheets/?cursor={cursor}&size=2")
    response_data = response.json()

    # Assert.
    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 2
    assert response_data["has_previous"] is True


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_last_page_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=10")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["has_next"] is False
    assert response_data["next_cursor"] is None


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_with_search_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?search=python&size=5")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["title"] == "Python Basics"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_with_tag_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?tag=fastapi&size=5")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["title"] == "FastAPI Tutorial"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_private_not_visible_for_anonymous(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=10")
    response_data = response.json()

    titles = [item["title"] for item in response_data["items"]]
    assert "Private Cheatsheet" not in titles


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_sorting_asc_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/cheatsheets/?sort_by=title&sort_order=asc&size=10"
    )
    response_data = response.json()

    titles = [item["title"] for item in response_data["items"]]
    assert titles == sorted(titles)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_invalid_cursor_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?cursor=invalid&size=2")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_search_suggestions_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/suggestions?query=py&limit=5")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["titles"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_search_suggestions_no_results(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/suggestions?query=xyz123&limit=5")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["titles"]) == 0


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_sorting_desc_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/cheatsheets/?sort_by=created_at&sort_order=desc&size=10"
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    titles = [item["title"] for item in response_data["items"]]
    assert titles == [
        "Django Web Framework",
        "PostgreSQL Guide",
        "FastAPI Tutorial",
        "Python Basics",
    ]
    assert response_data["items"][0]["title"] == "Django Web Framework"
    assert response_data["items"][-1]["title"] == "Python Basics"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_sorting_by_title_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/cheatsheets/?sort_by=title&sort_order=asc&size=10"
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    titles = [item["title"] for item in response_data["items"]]
    assert titles == sorted(titles)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_sorting_by_updated_at_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/cheatsheets/?sort_by=updated_at&sort_order=desc&size=10"
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 4
    assert response_data["items"][0]["title"] == "Django Web Framework"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_invalid_sort_field_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?sort_by=invalid_field&size=2")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_invalid_sort_order_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?sort_order=invalid&size=2")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_with_search_and_tag_combined_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?search=python&tag=python&size=5")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["title"] == "Python Basics"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_minimum_page_size_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=1")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 1
    assert response_data["has_next"] is True
    assert response_data["next_cursor"] is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_maximum_page_size_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=100")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 4
    assert response_data["has_next"] is False
    assert response_data["next_cursor"] is None


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_size_exceeds_limit_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=101")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_size_zero_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?size=0")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_search_too_short_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?search=a&size=5")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_search_only_whitespace_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?search=   &size=5")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_list_cheatsheets_pagination_with_tag_filter_was_successful(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/?tag=python&size=2")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["title"] == "Python Basics"
    assert response_data["has_next"] is False


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_search_suggestions_limit_exceeds_maximum_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/suggestions?query=py&limit=11")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_search_suggestions_empty_query_was_bad_request(
    populate_db_for_cheatsheet_list: None,
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/cheatsheets/suggestions?query=&limit=5")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
