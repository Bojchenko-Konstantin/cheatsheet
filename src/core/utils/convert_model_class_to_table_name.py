CLASS_SUFFIX = "Model"
NAME_DELIMITER = "_"


def convert_model_class_to_table_name(class_name: str) -> str:
    """
    >>> convert_model_class_to_table_name("CheatsheetModel")
    'cheatsheet'
    >>> convert_model_class_to_table_name("TagModel")
    'tag'
    """

    modified_class_name = _remove_class_suffix(class_name)
    table_name_chars = _collect_snake_case_chars(modified_class_name)
    table_name = _assemble_table_name_chars(table_name_chars)

    return table_name


def _remove_class_suffix(class_name: str) -> str:
    return class_name.replace(CLASS_SUFFIX, "")


def _collect_snake_case_chars(class_name: str) -> list[str]:
    chars: list[str] = []
    for char_index, current_char in enumerate(class_name):
        # Check that chars are not part of the abbreviation and then add the delimeter.
        if _is_valid_capital_char(char_index, current_char):
            next_char_index = char_index + 1
            is_next_char_capital_or_name_end = _is_next_char_word_end(
                next_char_index, class_name
            )
            previous_char = class_name[char_index - 1]

            _add_delimiter_to_table_chars(
                previous_char, is_next_char_capital_or_name_end, chars
            )

        chars.append(current_char.lower())
    return chars


def _assemble_table_name_chars(chars: list[str]) -> str:
    return "".join(chars)


def _is_valid_capital_char(char_index: int, current_char: str) -> bool:
    return char_index > 0 and current_char.isupper()


def _is_next_char_word_end(char_index: int, class_name: str) -> bool:
    return char_index >= len(class_name) or class_name[char_index].isupper()


def _add_delimiter_to_table_chars(
    previous_char: str,
    is_next_char_capital_or_name_end: bool,
    table_name_chars: list[str],
) -> None:
    if not _is_char_group_abbreviation(previous_char, is_next_char_capital_or_name_end):
        table_name_chars.append(NAME_DELIMITER)


def _is_char_group_abbreviation(
    previous_char: str, is_capital_char_or_name_end: bool
) -> bool:
    return previous_char.isupper() and is_capital_char_or_name_end
