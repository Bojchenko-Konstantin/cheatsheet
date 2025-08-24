import pytest

from src.core.utils import convert_model_class_to_table_name

EXPECTED_RESULTS = [
    (0, "http_request"),
    (1, "fast_api"),
    (2, "cheatsheet_to_tag"),
    (3, "http_reques2t"),
]


@pytest.mark.parametrize("index, expected_name", EXPECTED_RESULTS)
def test_convert_model_class_to_table_name(index: int, expected_name: str):
    results = [
        convert_model_class_to_table_name(model_name)
        for model_name in [
            "HTTPRequestModel",
            "FastAPI",
            "CheatsheetToTagModel",
            "HTTPReques2t",
        ]
    ]
    assert results[index] == expected_name
