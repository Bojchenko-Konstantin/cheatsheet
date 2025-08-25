import pytest

from src.core.utils import convert_model_class_to_table_name

TEST_CASES = [
    ("HTTPRequestModel", "http_request"),
    ("FastAPI", "fast_api"),
    ("CheatsheetToTagModel", "cheatsheet_to_tag"),
    ("HTTPReques2t", "http_reques2t"),
]


@pytest.mark.parametrize("input_name, expected_result", TEST_CASES)
def test_convert_model_class_to_table_name(input_name: str, expected_result: str):
    assert convert_model_class_to_table_name(input_name) == expected_result
