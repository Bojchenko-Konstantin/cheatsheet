def model_class_to_table_name(model_class_name: str) -> str:
    """
    >>> model_class_to_table_name("CheatsheetModel")
    'cheatsheet'
    >>> model_class_to_table_name("TagModel")
    'tag'
    """
    if model_class_name.endswith("Model"):
        class_name_without_model = model_class_name[:-5]
    else:
        class_name_without_model = model_class_name

    table_name_chars = []
    for char_index, current_char in enumerate(class_name_without_model):
        if char_index > 0 and current_char.isupper():
            next_char_index = char_index + 1
            is_next_char_upper = (
                next_char_index >= len(class_name_without_model)
                or class_name_without_model[next_char_index].isupper()
            )
            previous_char = class_name_without_model[char_index - 1]

            if previous_char.isupper() and is_next_char_upper:
                pass
            else:
                table_name_chars.append("_")

        table_name_chars.append(current_char.lower())

    return "".join(table_name_chars)
