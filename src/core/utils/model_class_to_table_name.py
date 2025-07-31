def model_class_to_table_name(model_class: str) -> str:
    """
    >>> model_class_to_table_name("CheatsheetModel")
    'cheatsheet'
    >>> model_class_to_table_name("TagModel")
    'tag'
    """
    if model_class.endswith("Model"):
        model_class = model_class[:-5]

    chars = []
    for c_idx, char in enumerate(model_class):
        if c_idx and char.isupper():
            nxt_idx = c_idx + 1
            flag = (
                nxt_idx >= len(model_class) or model_class[nxt_idx].isupper()
            )
            prev_char = model_class[c_idx - 1]
            if prev_char.isupper() and flag:
                pass
            else:
                chars.append("_")
        chars.append(char.lower())
    return "".join(chars)
