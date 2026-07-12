def multiple_string_replace(input_string: str, replacements: dict[str, str]) -> str:
    """Replace multiple substrings in a string in a single call.

    Each key in the replacements mapping is replaced with its corresponding value,
    applied in iteration order over the mapping.

    Args:
        input_string: The original string where replacements will be made.
        replacements: A mapping of substrings to replace to the substrings to replace
            them with.

    Returns:
        The modified string with all specified replacements made.
    """
    for old_substring, new_substring in replacements.items():
        input_string = input_string.replace(old_substring, new_substring)
    return input_string
